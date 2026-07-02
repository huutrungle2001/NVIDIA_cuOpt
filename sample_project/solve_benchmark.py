import sys
import time
import os
import numpy as np
import multiprocessing

# Try imports
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

try:
    import pulp
    HAS_PULP = True
except ImportError:
    HAS_PULP = False

def parse_instance(filepath):
    num_trucks = 10
    capacity = 1300.0
    coords = []
    demands = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if "," in line:
            parts = line.split(",")
            key = parts[0].strip()
            val = parts[1].strip()
            if key == "NUM TRUCKS":
                num_trucks = int(val)
            elif key == "TRUCK CAP":
                capacity = float(val)
        else:
            parts = line.split()
            if len(parts) == 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    demand = float(parts[3])
                    coords.append((x, y))
                    demands.append(demand)
                except ValueError:
                    continue
                
    return num_trucks, capacity, coords, demands

def calculate_distance_matrix(coords):
    n = len(coords)
    matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            matrix[i][j] = np.sqrt(dx*dx + dy*dy)
    return matrix

def run_cuopt(n_locations, n_fleet, capacity, distances, demands, timeout):
    if not HAS_CUOPT:
        return None, None, "Not installed"
        
    try:
        solve_start = time.perf_counter()
        cost_matrix = cudf.DataFrame(distances)
        dm = routing.DataModel(n_locations=n_locations, n_fleet=n_fleet, n_orders=n_locations - 1)
        dm.add_cost_matrix(cost_matrix)
        dm.set_order_locations(cudf.Series(range(1, n_locations), dtype=np.int32))
        
        order_demands = cudf.Series(demands[1:], dtype=np.int32)
        truck_capacities = cudf.Series([capacity] * n_fleet, dtype=np.int32)
        dm.add_capacity_dimension("demand", order_demands, truck_capacities)
        
        truck_starts = cudf.Series([0] * n_fleet, dtype=np.int32)
        truck_ends = cudf.Series([0] * n_fleet, dtype=np.int32)
        dm.set_vehicle_locations(truck_starts, truck_ends)
        
        settings = routing.SolverSettings()
        settings.set_time_limit(int(timeout))
        
        solution = routing.Solve(dm, settings)
        solve_end = time.perf_counter()
        
        status = solution.get_status()
        if status == 0:
            return solution.get_total_objective(), (solve_end - solve_start), "Success"
        else:
            return None, None, f"Solver status: {status} ({solution.get_error_message()})"
    except Exception as e:
        return None, None, str(e)

def run_gurobi(n_locations, n_fleet, capacity, distances, demands, timeout):
    if not HAS_GUROBI:
        return None, None, "Not installed"
        
    try:
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        
        m = gp.Model("VRP", env=env)
        m.setParam("TimeLimit", float(timeout))
        
        x = m.addVars(n_locations, n_locations, vtype=GRB.BINARY, name="x")
        u = m.addVars(range(1, n_locations), lb=[demands[i] for i in range(1, n_locations)], ub=capacity, name="u")
        
        m.setObjective(gp.quicksum(distances[i, j] * x[i, j] for i in range(n_locations) for j in range(n_locations)), GRB.MINIMIZE)
        
        for i in range(n_locations):
            m.addConstr(x[i, i] == 0)
            
        for j in range(1, n_locations):
            m.addConstr(gp.quicksum(x[i, j] for i in range(n_locations)) == 1)
            
        for i in range(1, n_locations):
            m.addConstr(gp.quicksum(x[i, j] for j in range(n_locations)) == 1)
            
        m.addConstr(gp.quicksum(x[0, j] for j in range(1, n_locations)) <= n_fleet)
        m.addConstr(gp.quicksum(x[i, 0] for i in range(1, n_locations)) <= n_fleet)
        
        for i in range(1, n_locations):
            for j in range(1, n_locations):
                if i != j:
                    m.addConstr(u[i] - u[j] + capacity * x[i, j] <= capacity - demands[j])
                    
        solve_start = time.perf_counter()
        m.optimize()
        solve_end = time.perf_counter()
        
        if m.Status == GRB.OPTIMAL:
            return m.ObjVal, (solve_end - solve_start), "Success (Optimal)"
        elif m.Status == GRB.TIME_LIMIT:
            try:
                return m.ObjVal, (solve_end - solve_start), "Timeout (Feasible solution found)"
            except AttributeError:
                return None, None, "Timeout (No feasible solution found)"
        else:
            return None, None, f"Gurobi Status: {m.Status}"
    except gp.GurobiError as e:
        return None, None, f"Gurobi Error: {e.message}"
    except Exception as e:
        return None, None, str(e)

def run_cplex(n_locations, n_fleet, capacity, distances, demands, timeout):
    if not HAS_PULP:
        return None, None, "PuLP not installed"
        
    cplex_path = "/opt/ibm/ILOG/CPLEX_Studio2211/cplex/bin/x86-64_linux/cplex"
    if not os.path.exists(cplex_path):
        return None, None, f"CPLEX executable not found at {cplex_path}"
        
    try:
        prob = pulp.LpProblem("VRP", pulp.LpMinimize)
        x = pulp.LpVariable.dicts("x", ((i, j) for i in range(n_locations) for j in range(n_locations)), cat='Binary')
        u = pulp.LpVariable.dicts("u", (i for i in range(1, n_locations)), lowBound=0, upBound=capacity, cat='Continuous')
        
        prob += pulp.lpSum(distances[i][j] * x[i, j] for i in range(n_locations) for j in range(n_locations))
        
        for i in range(n_locations):
            prob += x[i, i] == 0
            
        for j in range(1, n_locations):
            prob += pulp.lpSum(x[i, j] for i in range(n_locations)) == 1
            
        for i in range(1, n_locations):
            prob += pulp.lpSum(x[i, j] for j in range(n_locations)) == 1
            
        prob += pulp.lpSum(x[0, j] for j in range(1, n_locations)) <= n_fleet
        prob += pulp.lpSum(x[i, 0] for i in range(1, n_locations)) <= n_fleet
        
        for i in range(1, n_locations):
            prob += u[i] >= demands[i]
            
        for i in range(1, n_locations):
            for j in range(1, n_locations):
                if i != j:
                    prob += u[i] - u[j] + capacity * x[i, j] <= capacity - demands[j]
                    
        solver = pulp.CPLEX_CMD(path=cplex_path, timeLimit=float(timeout), msg=False)
        
        solve_start = time.perf_counter()
        status = prob.solve(solver)
        solve_end = time.perf_counter()
        
        if status == pulp.LpStatusOptimal:
            return pulp.value(prob.objective), (solve_end - solve_start), "Success (Optimal)"
        else:
            return None, None, f"CPLEX status: {pulp.LpStatus[status]}"
    except Exception as e:
        return None, None, str(e)

def solve_worker(solver_name, solve_func, args, return_dict):
    if os.path.exists("/home/orlab/gurobi_license.lic"):
        os.environ["GRB_LICENSE_FILE"] = "/home/orlab/gurobi_license.lic"
    try:
        obj, elapsed, msg = solve_func(*args)
        return_dict[solver_name] = (obj, elapsed, msg)
    except Exception as e:
        return_dict[solver_name] = (None, None, str(e))

if __name__ == "__main__":
    # Use 'spawn' start method to prevent CUDA initialization errors in child processes
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    if len(sys.argv) < 2:
        print("Usage: python solve_benchmark.py <instance_file> [timeout_seconds]")
        sys.exit(1)
        
    filepath = sys.argv[1]
    timeout = 60.0
    if len(sys.argv) >= 3:
        timeout = float(sys.argv[2])
        
    print(f"Parsing instance file: {filepath}...")
    num_trucks, capacity, coords, demands = parse_instance(filepath)
    n_locations = len(coords)
    
    print(f"Loaded {n_locations} locations (depot + {n_locations-1} customers).")
    print(f"Fleet: {num_trucks} trucks, Capacity per truck: {capacity}")
    print(f"Time limit set to: {timeout} seconds")
    
    distances = calculate_distance_matrix(coords)
    
    print("\nStarting Parallel Benchmarks (Multiprocessing)...")
    print("--------------------------------------------------")
    
    # Use multiprocessing manager to gather results from child processes
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    
    solvers = [
        ("Gurobi", run_gurobi),
        ("CPLEX", run_cplex),
        ("cuOpt", run_cuopt)
    ]
    
    processes = []
    for name, func in solvers:
        p = multiprocessing.Process(
            target=solve_worker,
            args=(name, func, (n_locations, num_trucks, capacity, distances, demands, timeout), return_dict)
        )
        processes.append(p)
        p.start()
        print(f"Launched {name} solver in background process...")
        
    # Wait for all processes to finish
    for p in processes:
        p.join()
        
    print("\nBenchmarks Completed!")
    print("--------------------------------------------------")
    
    for name, _ in solvers:
        if name in return_dict:
            obj, elapsed, msg = return_dict[name]
            if obj is not None:
                print(f"{name:<8}: Objective = {obj:.2f}, Time = {elapsed:.4f} s ({msg})")
            else:
                print(f"{name:<8}: Failed ({msg})")
        else:
            print(f"{name:<8}: Failed (No return data)")
    print("--------------------------------------------------")
