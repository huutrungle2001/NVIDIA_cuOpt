import os
import time
import numpy as np

try:
    import cudf
    from cuopt import routing
    HAS_CUOPT = True
except ImportError:
    HAS_CUOPT = False

from sample_project.gctsp.parser import parse_gctsp

def solve_cuopt_tsp(node_subset, distance_matrix):
    """
    Solves a standard TSP over a subset of nodes using cuOpt on the GPU.
    Returns the optimal sequence (in original node indices) and tour distance.
    """
    if not HAS_CUOPT:
        # Fallback to simple nearest neighbor if cuOpt is not installed (for local mac test safety)
        # Nearest neighbor tsp fallback
        tour = [0]
        unvisited = set(node_subset)
        if 0 in unvisited:
            unvisited.remove(0)
        curr = 0
        dist_sum = 0.0
        while unvisited:
            next_node = min(unvisited, key=lambda x: distance_matrix[curr, x])
            dist_sum += distance_matrix[curr, next_node]
            tour.append(next_node)
            unvisited.remove(next_node)
            curr = next_node
        dist_sum += distance_matrix[curr, 0]
        tour.append(0)
        return tour, dist_sum

    K = len(node_subset)
    if K <= 1:
        return [0, 0], 0.0
        
    # Extract the K x K submatrix
    sub_dist = distance_matrix[np.ix_(node_subset, node_subset)].astype(np.float32)
    
    dm = routing.DataModel(n_locations=K, n_fleet=1, n_orders=K-1)
    dm.add_cost_matrix(cudf.DataFrame(sub_dist))
    dm.set_order_locations(cudf.Series(range(1, K), dtype=np.int32))
    dm.set_vehicle_locations(cudf.Series([0], dtype=np.int32), cudf.Series([0], dtype=np.int32))
    
    settings = routing.SolverSettings()
    settings.set_time_limit(0.1) # extremely fast solve (100 ms)
    
    sol = routing.Solve(dm, settings)
    if sol.get_status() == 0:
        route_df = sol.get_route()
        nodes = route_df['location'].to_arrow().to_pylist()
        # Map sub-tour indices back to original node indices
        tour = [node_subset[0]] + [node_subset[idx] for idx in nodes] + [node_subset[0]]
        return tour, sol.get_total_objective()
    else:
        # Fallback if solver fails
        tour = node_subset + [node_subset[0]]
        cost = sum(distance_matrix[tour[i], tour[i+1]] for i in range(len(tour)-1))
        return tour, cost

def get_covered_count(facility_subset, customer_nodes, c_to_cov):
    """
    Calculates the total number of customers covered by the facility subset.
    """
    covered = set()
    fac_set = set(facility_subset)
    for c in customer_nodes:
        # If any covering facility of customer c is in our subset
        for j in c_to_cov[c]:
            if j in fac_set:
                covered.add(c)
                break
    return len(covered), covered

def solve_gctsp_hybrid(instance_path, max_iterations=500):
    """
    Solves the GCTSP using Method B (Hybrid Greedy Set Cover + local search + cuOpt GPU TSP).
    """
    start_time = time.perf_counter()
    data = parse_gctsp(instance_path)
    
    name = data['name']
    num_nodes = data['num_nodes']
    depot = data['depot']
    num_customers = data['num_customers']
    quota = data['quota']
    facility_nodes = data['facility_nodes']
    customer_nodes = data['customer_nodes']
    covering_sets = data['covering_sets']
    distances = data['distances']
    
    # Map customer node index to its covering facility list
    c_to_cov = {}
    for idx, c in enumerate(customer_nodes):
        c_to_cov[c] = list(covering_sets[idx])
        
    # Step 1: Initial Feasible Solution using Greedy Set Cover
    active_subset = []
    uncovered = set(customer_nodes)
    
    while len(customer_nodes) - len(uncovered) < quota:
        # Find facility that covers the most remaining uncovered customers
        best_fac = None
        best_cover = -1
        
        for f in facility_nodes:
            if f in active_subset:
                continue
            # Count how many uncovered customers this facility covers
            cover_count = sum(1 for c in uncovered if f in c_to_cov[c])
            if cover_count > best_cover:
                best_cover = cover_count
                best_fac = f
                
        if best_fac is None or best_cover <= 0:
            # Not enough facilities to cover the quota
            break
            
        active_subset.append(best_fac)
        # Remove covered customers from the uncovered set
        covered_by_best = {c for c in uncovered if best_fac in c_to_cov[c]}
        uncovered -= covered_by_best
        
    # Solve initial TSP
    node_subset = [depot] + active_subset
    best_sequence, best_cost = solve_cuopt_tsp(node_subset, distances)
    best_subset = active_subset[:]
    
    # Step 2: Local Search Refinement Loop
    rng = np.random.default_rng(42)
    
    for iteration in range(max_iterations):
        improved = False
        
        # Operator 1: Swap (Exchange an active facility with an inactive one)
        if len(best_subset) > 0 and len(facility_nodes) > len(best_subset):
            # Select random active and inactive facilities
            a = rng.choice(best_subset)
            inactive = list(set(facility_nodes) - set(best_subset))
            b = rng.choice(inactive)
            
            # Form candidate subset
            candidate_subset = [f for f in best_subset if f != a] + [b]
            covered_count, _ = get_covered_count(candidate_subset, customer_nodes, c_to_cov)
            
            if covered_count >= quota:
                node_subset = [depot] + candidate_subset
                new_sequence, new_cost = solve_cuopt_tsp(node_subset, distances)
                if new_cost < best_cost:
                    best_cost = new_cost
                    best_subset = candidate_subset[:]
                    best_sequence = new_sequence[:]
                    improved = True
                    
        # Operator 2: Drop (Attempt to remove a facility to reduce travel cost)
        if len(best_subset) > 1 and not improved:
            a = rng.choice(best_subset)
            candidate_subset = [f for f in best_subset if f != a]
            covered_count, _ = get_covered_count(candidate_subset, customer_nodes, c_to_cov)
            
            if covered_count >= quota:
                node_subset = [depot] + candidate_subset
                new_sequence, new_cost = solve_cuopt_tsp(node_subset, distances)
                if new_cost < best_cost:
                    best_cost = new_cost
                    best_subset = candidate_subset[:]
                    best_sequence = new_sequence[:]
                    improved = True
                    
    # Compute final coverage
    final_covered_cnt, final_covered_list = get_covered_count(best_subset, customer_nodes, c_to_cov)
    elapsed = time.perf_counter() - start_time
    
    return {
        'status': "SUCCESS",
        'objective': best_cost,
        'sequence': best_sequence,
        'covered_count': final_covered_cnt,
        'covered_list': list(final_covered_list),
        'time_s': elapsed
    }

if __name__ == "__main__":
    import sys
    path = "/Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/data/gctsp/tsplib_small/burma14_t30_p50.gctsp"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    res = solve_gctsp_hybrid(path, max_iterations=200)
    print(res)
