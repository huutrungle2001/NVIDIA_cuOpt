import time
import numpy as np

# Try importing cuOpt
try:
    import cudf
    from cuopt import routing
    HAS_CUOPT = True
except ImportError:
    HAS_CUOPT = False

# Try importing CPLEX
try:
    import cplex
    HAS_CPLEX = True
except ImportError:
    HAS_CPLEX = False

# Problem Data
n_locations = 4
n_fleet = 2
n_orders = 3
capacity = 40

# Cost matrix
distances = np.array([
    [0.0, 10.0, 15.0, 20.0],  # Depot (0)
    [10.0, 0.0, 35.0, 25.0],  # Store A (1)
    [15.0, 35.0, 0.0, 30.0],  # Store B (2)
    [20.0, 25.0, 30.0, 0.0]   # Store C (3)
], dtype=np.float32)

demands = [15, 30, 20] # For Stores A, B, C (indices 1, 2, 3)

def run_cuopt():
    if not HAS_CUOPT:
        print("cuOpt is not available.")
        return None, None
        
    cost_matrix = cudf.DataFrame(distances)
    dm = routing.DataModel(n_locations=n_locations, n_fleet=n_fleet, n_orders=n_orders)
    dm.add_cost_matrix(cost_matrix)
    dm.set_order_locations(cudf.Series([1, 2, 3], dtype=np.int32))
    
    order_demands = cudf.Series(demands, dtype=np.int32)
    truck_capacities = cudf.Series([capacity, capacity], dtype=np.int32)
    dm.add_capacity_dimension("demand", order_demands, truck_capacities)
    
    truck_starts = cudf.Series([0, 0], dtype=np.int32)
    truck_ends = cudf.Series([0, 0], dtype=np.int32)
    dm.set_vehicle_locations(truck_starts, truck_ends)
    
    settings = routing.SolverSettings()
    settings.set_time_limit(5)
    
    # Solve and measure solve time
    solve_start = time.perf_counter()
    solution = routing.Solve(dm, settings)
    solve_end = time.perf_counter()
    
    total_time = solve_end - solve_start
    status = solution.get_status()
    
    if status == 0:
        obj = solution.get_total_objective()
        return obj, total_time
    else:
        return None, None

def run_cplex():
    if not HAS_CPLEX:
        print("CPLEX is not available.")
        return None, None
        
    # Model VRP in CPLEX using Miller-Tucker-Zemlin formulation
    c = cplex.Cplex()
    c.set_results_stream(None)  # Suppress CPLEX logs
    c.set_log_stream(None)
    
    c.objective.set_sense(c.objective.sense.minimize)
    
    # Variables: x_ij for i,j in 0..3 (binary)
    # u_i for i in 1..3 (continuous) representing current vehicle load after visiting node i
    var_names = []
    var_types = []
    var_objs = []
    
    # Edge variables x_ij
    for i in range(4):
        for j in range(4):
            var_names.append(f"x_{i}_{j}")
            var_types.append(c.variables.type.binary)
            var_objs.append(float(distances[i][j]))
            
    # Load variables u_i
    for i in range(1, 4):
        var_names.append(f"u_{i}")
        var_types.append(c.variables.type.continuous)
        var_objs.append(0.0)
        
    c.variables.add(obj=var_objs, types=var_types, names=var_names)
    
    # Set bounds for u_i: demand_i <= u_i <= Capacity
    for i in range(1, 4):
        idx = i - 1
        c.variables.set_lower_bounds(f"u_{i}", float(demands[idx]))
        c.variables.set_upper_bounds(f"u_{i}", float(capacity))
        
    # Constraints:
    # 1. No self-loops: x_ii = 0
    for i in range(4):
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=[f"x_{i}_{i}"], val=[1.0])],
            senses=["E"],
            rhs=[0.0]
        )
        
    # 2. Customer in-degree = 1
    for j in range(1, 4):
        ind = [f"x_{i}_{j}" for i in range(4)]
        val = [1.0] * 4
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=ind, val=val)],
            senses=["E"],
            rhs=[1.0]
        )
        
    # 3. Customer out-degree = 1
    for i in range(1, 4):
        ind = [f"x_{i}_{j}" for j in range(4)]
        val = [1.0] * 4
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=ind, val=val)],
            senses=["E"],
            rhs=[1.0]
        )
        
    # 4. Fleet starts from Depot (outgoing sum <= n_fleet)
    ind = [f"x_0_{j}" for j in range(1, 4)]
    val = [1.0] * 3
    c.linear_constraints.add(
        lin_expr=[cplex.SparsePair(ind=ind, val=val)],
        senses=["L"],
        rhs=[float(n_fleet)]
    )
    
    # 5. Fleet returns to Depot (incoming sum <= n_fleet)
    ind = [f"x_{i}_0" for i in range(1, 4)]
    val = [1.0] * 3
    c.linear_constraints.add(
        lin_expr=[cplex.SparsePair(ind=ind, val=val)],
        senses=["L"],
        rhs=[float(n_fleet)]
    )
    
    # 6. Miller-Tucker-Zemlin capacity tracking:
    # u_j >= u_i + demand_j - Q * (1 - x_ij) => u_i - u_j + Q * x_ij <= Q - demand_j
    for i in range(1, 4):
        for j in range(1, 4):
            if i != j:
                dem_j = demands[j-1]
                ind = [f"u_{i}", f"u_{j}", f"x_{i}_{j}"]
                val = [1.0, -1.0, float(capacity)]
                c.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=ind, val=val)],
                    senses=["L"],
                    rhs=[float(capacity - dem_j)]
                )
                
    # Solve and measure solve time
    solve_start = time.perf_counter()
    c.solve()
    solve_end = time.perf_counter()
    
    total_time = solve_end - solve_start
    status = c.solution.get_status_string()
    
    if "optimal" in status.lower():
        obj = c.solution.get_objective_value()
        return obj, total_time
    else:
        print(f"CPLEX failed: {status}")
        return None, None

if __name__ == "__main__":
    print("==================================================")
    print("   cuOpt vs CPLEX VRP Solver Comparison")
    print("==================================================\n")
    
    cuopt_obj, cuopt_time = run_cuopt()
    cplex_obj, cplex_time = run_cplex()
    
    if cuopt_obj is not None:
        print(f"NVIDIA cuOpt:")
        print(f"  - Objective Value: {cuopt_obj:.2f}")
        print(f"  - Solve Time:      {cuopt_time * 1000:.3f} ms")
    else:
        print("cuOpt failed to run.")
        
    print()
    
    if cplex_obj is not None:
        print(f"IBM ILOG CPLEX:")
        print(f"  - Objective Value: {cplex_obj:.2f}")
        print(f"  - Solve Time:      {cplex_time * 1000:.3f} ms")
    else:
        print("CPLEX failed to run.")
        
    print("\n==================================================")
