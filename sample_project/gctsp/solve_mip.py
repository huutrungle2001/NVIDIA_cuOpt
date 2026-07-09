import os
import time
import pulp
from sample_project.gctsp.parser import parse_gctsp

def solve_gctsp_mip(instance_path, solver_name="cbc", time_limit=30):
    """
    Solves the GCTSP using Method A (Direct MILP formulation via PuLP).
    Supports Gurobi, CPLEX, and CBC backends.
    """
    print(f"Loading GCTSP instance: {instance_path}")
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
    
    # Vertices involved in the routing tour (facilities + depot)
    V_route = [depot] + facility_nodes
    
    # Map customer node index to its covering facility list
    # covering_sets is 0-indexed corresponding to sorted customer_nodes
    c_to_cov = {}
    for idx, c in enumerate(customer_nodes):
        c_to_cov[c] = list(covering_sets[idx])
        
    print(f"Problem: {name} | Nodes: {num_nodes} | Facilities: {len(facility_nodes)} | Customers: {num_customers} | Quota: {quota}")
    
    # Create the PuLP optimization problem
    prob = pulp.LpProblem("GCTSP_MIP", pulp.LpMinimize)
    
    # 1. Routing decision variables: x[i][j] = 1 if edge (i,j) is traveled
    x = pulp.LpVariable.dicts("x", (V_route, V_route), cat='Binary')
    
    # 2. Coverage decision variables: z[c][j] = 1 if customer c is allocated to visited facility j
    z = {}
    for c in customer_nodes:
        z[c] = {}
        for j in c_to_cov[c]:
            z[c][j] = pulp.LpVariable(f"z_{c}_{j}", cat='Binary')
            
    # 3. Subtour flow variables: u[i][j] = flow from i to j
    u = pulp.LpVariable.dicts("u", (V_route, V_route), lowBound=0, cat='Continuous')
    
    # Objective: Minimize total travel distance
    prob += pulp.lpSum(distances[i, j] * x[i][j] for i in V_route for j in V_route if i != j)
    
    # Constraints:
    # 1. Quota Target Constraint
    prob += pulp.lpSum(z[c][j] for c in customer_nodes for j in c_to_cov[c]) >= quota
    
    # 2. Single Coverage Allocation
    for c in customer_nodes:
        if c_to_cov[c]:
            prob += pulp.lpSum(z[c][j] for j in c_to_cov[c]) <= 1
            
    # 3. Depot Visit limit (Starts from depot)
    prob += pulp.lpSum(x[depot][j] for j in facility_nodes) == 1
    
    # 4. No self loops
    for i in V_route:
        prob += x[i][i] == 0
        
    # 5. In-degree / Out-degree balance
    for i in V_route:
        prob += pulp.lpSum(x[i][j] for j in V_route if j != i) == pulp.lpSum(x[j][i] for j in V_route if j != i)
        
    # 6. Facility coverage visit limit: customer c can allocate to facility j only if j is visited
    for c in customer_nodes:
        for j in c_to_cov[c]:
            prob += z[c][j] <= pulp.lpSum(x[k][j] for k in V_route if k != j)
            
    # 7. Subtour elimination (Flow constraints)
    # Total flow out of depot equals total covered customers
    prob += pulp.lpSum(u[depot][j] for j in facility_nodes) == pulp.lpSum(z[c][j] for c in customer_nodes for j in c_to_cov[c])
    
    # Flow conservation at each facility
    for i in facility_nodes:
        prob += pulp.lpSum(u[j][i] for j in V_route if j != i) - pulp.lpSum(u[i][j] for j in V_route if j != i) == \
                pulp.lpSum(z[c][i] for c in customer_nodes if i in c_to_cov[c])
                
    # Flow back into depot is 0
    prob += pulp.lpSum(u[j][depot] for j in facility_nodes) == 0
    
    # Flow capacity bound on active edges (M = num_customers)
    for i in V_route:
        for j in V_route:
            if i != j:
                prob += u[i][j] <= num_customers * x[i][j]
                
    # Configure Solver
    if solver_name.lower() == "gurobi":
        if os.path.exists("/home/orlab/gurobi_license.lic"):
            os.environ["GRB_LICENSE_FILE"] = "/home/orlab/gurobi_license.lic"
        solver = pulp.GUROBI_CMD(timeLimit=time_limit, msg=True)
    elif solver_name.lower() == "cplex":
        cplex_path = "/opt/ibm/ILOG/CPLEX_Studio2211/cplex/bin/x86-64_linux/cplex"
        if os.path.exists(cplex_path):
            solver = pulp.CPLEX_CMD(path=cplex_path, timeLimit=time_limit, msg=True)
        else:
            solver = pulp.CPLEX_CMD(timeLimit=time_limit, msg=True)
    else:
        solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=False)
        
    # Solve
    start_time = time.perf_counter()
    status = prob.solve(solver)
    elapsed = time.perf_counter() - start_time
    
    # Extract results
    pulp_status = pulp.LpStatus[status]
    if pulp_status == "Optimal":
        # Trace sequence of visited facilities
        visited_edges = []
        for i in V_route:
            for j in V_route:
                if x[i][j].varValue is not None and x[i][j].varValue > 0.5:
                    visited_edges.append((i, j))
                    
        # Sort visited nodes into a sequence starting at depot 0
        curr = depot
        sequence = [depot]
        while True:
            next_node = None
            for edge in visited_edges:
                if edge[0] == curr:
                    next_node = edge[1]
                    break
            if next_node is None or next_node == depot:
                sequence.append(depot)
                break
            sequence.append(next_node)
            curr = next_node
            
        # Count actually covered customers
        covered_customers = []
        for c in customer_nodes:
            for j in c_to_cov[c]:
                if z[c][j].varValue is not None and z[c][j].varValue > 0.5:
                    covered_customers.append(c)
                    break
                    
        tour_cost = pulp.value(prob.objective)
        return {
            'status': "SUCCESS",
            'objective': tour_cost,
            'sequence': sequence,
            'covered_count': len(covered_customers),
            'covered_list': covered_customers,
            'time_s': elapsed
        }
    else:
        return {
            'status': f"FAILED ({pulp_status})",
            'objective': None,
            'sequence': None,
            'covered_count': 0,
            'covered_list': [],
            'time_s': elapsed
        }

if __name__ == "__main__":
    import sys
    path = "/Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/data/gctsp/tsplib_small/burma14_t30_p50.gctsp"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    res = solve_gctsp_mip(path, solver_name="cbc")
    print(res)
