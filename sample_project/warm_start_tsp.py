import sys
import time
import os
import numpy as np

try:
    import cudf
    from cuopt import routing
    HAS_CUOPT = True
except ImportError:
    HAS_CUOPT = False

try:
    import gurobipy as gp
    from gurobipy import GRB
    HAS_GUROBI = True
except ImportError:
    HAS_GUROBI = False

# Explicitly set Gurobi license path
if os.path.exists("/home/orlab/gurobi_license.lic"):
    os.environ["GRB_LICENSE_FILE"] = "/home/orlab/gurobi_license.lic"

def create_random_tsp(n_nodes):
    np.random.seed(42)
    coords = np.random.rand(n_nodes, 2) * 100.0
    matrix = np.zeros((n_nodes, n_nodes), dtype=np.float32)
    for i in range(n_nodes):
        for j in range(n_nodes):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            matrix[i][j] = np.sqrt(dx*dx + dy*dy)
    return coords, matrix

def solve_cuopt_tsp(n_nodes, distance_matrix):
    if not HAS_CUOPT:
        return None
        
    cost_df = cudf.DataFrame(distance_matrix)
    dm = routing.DataModel(n_locations=n_nodes, n_fleet=1, n_orders=n_nodes - 1)
    dm.add_cost_matrix(cost_df)
    dm.set_order_locations(cudf.Series(range(1, n_nodes), dtype=np.int32))
    
    # All vehicles start and end at Node 0
    dm.set_vehicle_locations(cudf.Series([0], dtype=np.int32), cudf.Series([0], dtype=np.int32))
    
    settings = routing.SolverSettings()
    settings.set_time_limit(1) # 1 second limit
    
    solve_start = time.perf_counter()
    solution = routing.Solve(dm, settings)
    solve_end = time.perf_counter()
    
    status = solution.get_status()
    if status == 0:
        route_df = solution.get_route()
        nodes = route_df['location'].to_arrow().to_pylist()
        # Ensure it contains the complete loop starting and ending at 0
        tour = [0] + nodes + [0]
        elapsed = solve_end - solve_start
        return tour, solution.get_total_objective(), elapsed
    else:
        print(f"cuOpt failed: {solution.get_error_message()}")
        return None

# Subtour elimination callback for Gurobi
def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:
        # Get active edges
        vals = model.cbGetSolution(model._vars)
        selected = gp.tuplelist((i, j) for i, j in model._vars.keys() if vals[i, j] > 0.5)
        # Find subtours
        unvisited = list(range(model._n_nodes))
        cycle = range(model._n_nodes + 1)
        while unvisited:
            thiscycle = []
            neighbors = unvisited
            while neighbors:
                current = neighbors[0]
                thiscycle.append(current)
                unvisited.remove(current)
                neighbors = [j for i, j in selected.select(current, '*') if j in unvisited]
            if len(thiscycle) < len(cycle):
                cycle = thiscycle
        # If subtour found, add constraint
        if len(cycle) < model._n_nodes:
            model.cbLazy(gp.quicksum(model._vars[i, j] for i in cycle for j in cycle if i != j) <= len(cycle) - 1)

def solve_gurobi_tsp(n_nodes, distance_matrix, warm_start_tour=None, time_limit=15):
    if not HAS_GUROBI:
        return None, None
        
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1) # Enable output to see MIP Start messages
    env.start()
    
    m = gp.Model("TSP", env=env)
    m.setParam("TimeLimit", time_limit)
    m.setParam("LazyConstraints", 1)
    
    m._n_nodes = n_nodes
    
    # Binary variables: x_ij
    x = m.addVars(n_nodes, n_nodes, vtype=GRB.BINARY, name="x")
    m._vars = x
    
    # Objective
    m.setObjective(gp.quicksum(distance_matrix[i, j] * x[i, j] for i in range(n_nodes) for j in range(n_nodes)), GRB.MINIMIZE)
    
    # Constraints
    # No self loops
    for i in range(n_nodes):
        m.addConstr(x[i, i] == 0)
        
    # In-degree = 1
    for j in range(n_nodes):
        m.addConstr(gp.quicksum(x[i, j] for i in range(n_nodes)) == 1)
        
    # Out-degree = 1
    for i in range(n_nodes):
        m.addConstr(gp.quicksum(x[i, j] for j in range(n_nodes)) == 1)
        
    # Apply warm start if provided
    if warm_start_tour is not None:
        print("\n---> Setting cuOpt Tour as Gurobi MIP Start...")
        # Reset all variable starts
        for i in range(n_nodes):
            for j in range(n_nodes):
                x[i, j].Start = 0
                
        # Set active edges from cuOpt tour
        for idx in range(len(warm_start_tour) - 1):
            u = warm_start_tour[idx]
            v = warm_start_tour[idx + 1]
            x[u, v].Start = 1.0
            
    # Optimize
    solve_start = time.perf_counter()
    m.optimize(subtourelim)
    solve_end = time.perf_counter()
    
    elapsed = solve_end - solve_start
    try:
        obj = m.ObjVal
    except AttributeError:
        obj = None
    return obj, elapsed

if __name__ == "__main__":
    n_nodes = 120
    print("==================================================")
    print(f"   cuOpt + Gurobi Hybrid Warm-Start TSP ({n_nodes} nodes)")
    print("==================================================\n")
    
    coords, matrix = create_random_tsp(n_nodes)
    
    # 1. Solve using cuOpt (Heuristic Warm Start)
    print("Step 1: Running cuOpt GPU heuristic...")
    cuopt_res = solve_cuopt_tsp(n_nodes, matrix)
    if cuopt_res is not None:
        tour, cuopt_obj, cuopt_time = cuopt_res
        print(f"[SUCCESS] cuOpt found feasible tour: length = {cuopt_obj:.2f} in {cuopt_time * 1000:.2f} ms")
    else:
        tour = None
        print("[WARNING] cuOpt failed or not available.")
        
    print("\n--------------------------------------------------")
    # 2. Run Gurobi without Warm Start
    print("Step 2: Solving with Gurobi (Cold Start)...")
    gurobi_cold_obj, gurobi_cold_time = solve_gurobi_tsp(n_nodes, matrix, warm_start_tour=None, time_limit=15)
    
    print("\n--------------------------------------------------")
    # 3. Run Gurobi with cuOpt Warm Start
    print("Step 3: Solving with Gurobi + cuOpt Warm Start...")
    gurobi_warm_obj, gurobi_warm_time = solve_gurobi_tsp(n_nodes, matrix, warm_start_tour=tour, time_limit=15)
    
    print("\n==================================================")
    print("                  FINAL RESULTS")
    print("==================================================")
    print(f"cuOpt Alone     : Obj = {cuopt_obj:.2f}, Time = {cuopt_time * 1000:.2f} ms")
    if gurobi_cold_obj is not None:
        print(f"Gurobi (Cold)   : Obj = {gurobi_cold_obj:.2f}, Time = {gurobi_cold_time:.2f} s")
    if gurobi_warm_obj is not None:
        print(f"Gurobi (Hybrid) : Obj = {gurobi_warm_obj:.2f}, Time = {gurobi_warm_time:.2f} s")
    print("==================================================")
