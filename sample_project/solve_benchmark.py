import sys
import time
import os
import numpy as np

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

# Explicitly point Gurobi to the academic license file if it exists
if os.path.exists("/home/orlab/gurobi_license.lic"):
    os.environ["GRB_LICENSE_FILE"] = "/home/orlab/gurobi_license.lic"

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

def run_cuopt(n_locations, n_fleet, capacity, distances, demands):
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
        settings.set_time_limit(10)
        
        solution = routing.Solve(dm, settings)
        solve_end = time.perf_counter()
        
        status = solution.get_status()
        if status == 0:
            return solution.get_total_objective(), (solve_end - solve_start), "Success"
        else:
            return None, None, f"Solver status: {status} ({solution.get_error_message()})"
    except Exception as e:
        return None, None, str(e)

def run_gurobi(n_locations, n_fleet, capacity, distances, demands):
    if not HAS_GUROBI:
        return None, None, "Not installed"
        
    try:
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        
        m = gp.Model("VRP", env=env)
        m.setParam("TimeLimit", 30)
        
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

def run_cplex(n_locations, n_fleet, capacity, distances, demands):
    if not HAS_PULP:
        return None, None, "PuLP not installed"
        
    cplex_path = "/opt/ibm/ILOG/CPLEX_Studio2211/cplex/bin/x86-64_linux/cplex"
    if not os.path.exists(cplex_path):
        return None, None, f"CPLEX executable not found at {cplex_path}"
        
    try:
        # Define the problem using PuLP
        prob = pulp.LpProblem("VRP", pulp.LpMinimize)
        
        # Variables: x_ij binary
        x = pulp.LpVariable.dicts("x", ((i, j) for i in range(n_locations) for j in range(n_locations)), cat='Binary')
        
        # Variables: u_i continuous
        u = pulp.LpVariable.dicts("u", (i for i in range(1, n_locations)), lowBound=0, upBound=capacity, cat='Continuous')
        
        # Objective
        prob += pulp.lpSum(distances[i][j] * x[i, j] for i in range(n_locations) for j in range(n_locations))
        
        # Constraints:
        # 1. No self loops
        for i in range(n_locations):
            prob += x[i, i] == 0
            
        # 2. In-degree = 1
        for j in range(1, n_locations):
            prob += pulp.lpSum(x[i, j] for i in range(n_locations)) == 1
            
        # 3. Out-degree = 1
        for i in range(1, n_locations):
            prob += pulp.lpSum(x[i, j] for j in range(n_locations)) == 1
            
        # 4. Fleet limit outgoing from depot
        prob += pulp.lpSum(x[0, j] for j in range(1, n_locations)) <= n_fleet
        
        # 5. Fleet limit incoming to depot
        prob += pulp.lpSum(x[i, 0] for i in range(1, n_locations)) <= n_fleet
        
        # 6. Set bounds on u_i: demand_i <= u_i
        for i in range(1, n_locations):
            prob += u[i] >= demands[i]
            
        # 7. MTZ capacity constraints
        for i in range(1, n_locations):
            for j in range(1, n_locations):
                if i != j:
                    prob += u[i] - u[j] + capacity * x[i, j] <= capacity - demands[j]
                    
        # Run the solver via Command Line Interface (uses full licensed binary)
        solver = pulp.CPLEX_CMD(path=cplex_path, timeLimit=30, msg=False)
        
        solve_start = time.perf_counter()
        status = prob.solve(solver)
        solve_end = time.perf_counter()
        
        if status == pulp.LpStatusOptimal:
            return pulp.value(prob.objective), (solve_end - solve_start), "Success (Optimal)"
        else:
            return None, None, f"CPLEX status: {pulp.LpStatus[status]}"
    except Exception as e:
        return None, None, str(e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solve_benchmark.py <instance_file>")
        sys.exit(1)
        
    filepath = sys.argv[1]
    
    print(f"Parsing instance file: {filepath}...")
    num_trucks, capacity, coords, demands = parse_instance(filepath)
    n_locations = len(coords)
    
    print(f"Loaded {n_locations} locations (depot + {n_locations-1} customers).")
    print(f"Fleet: {num_trucks} trucks, Capacity per truck: {capacity}")
    
    distances = calculate_distance_matrix(coords)
    
    print("\nRunning Benchmarks...")
    print("--------------------------------------------------")
    
    # Gurobi
    g_obj, g_time, g_msg = run_gurobi(n_locations, num_trucks, capacity, distances, demands)
    if g_obj is not None:
        print(f"Gurobi:  Objective = {g_obj:.2f}, Time = {g_time:.4f} s ({g_msg})")
    else:
        print(f"Gurobi:  Failed ({g_msg})")
        
    # CPLEX
    c_obj, c_time, c_msg = run_cplex(n_locations, num_trucks, capacity, distances, demands)
    if c_obj is not None:
        print(f"CPLEX:   Objective = {c_obj:.2f}, Time = {c_time:.4f} s ({c_msg})")
    else:
        print(f"CPLEX:   Failed ({c_msg})")
        
    # cuOpt
    cu_obj, cu_time, cu_msg = run_cuopt(n_locations, num_trucks, capacity, distances, demands)
    if cu_obj is not None:
        print(f"cuOpt:   Objective = {cu_obj:.2f}, Time = {cu_time:.4f} s ({cu_msg})")
    else:
        print(f"cuOpt:   Failed ({cu_msg})")
    print("--------------------------------------------------")
