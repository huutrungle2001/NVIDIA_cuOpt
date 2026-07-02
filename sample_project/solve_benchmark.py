import sys
import time
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
    import cplex
    HAS_CPLEX = True
except ImportError:
    HAS_CPLEX = False

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
    if not HAS_CPLEX:
        return None, None, "Not installed"
        
    try:
        c = cplex.Cplex()
        c.set_results_stream(None)
        c.set_log_stream(None)
        c.parameters.timelimit.set(30.0)
        
        c.objective.set_sense(c.objective.sense.minimize)
        
        var_names = []
        var_types = []
        var_objs = []
        
        for i in range(n_locations):
            for j in range(n_locations):
                var_names.append(f"x_{i}_{j}")
                var_types.append(c.variables.type.binary)
                var_objs.append(float(distances[i][j]))
                
        for i in range(1, n_locations):
            var_names.append(f"u_{i}")
            var_types.append(c.variables.type.continuous)
            var_objs.append(0.0)
            
        c.variables.add(obj=var_objs, types=var_types, names=var_names)
        
        for i in range(1, n_locations):
            c.variables.set_lower_bounds(f"u_{i}", float(demands[i]))
            c.variables.set_upper_bounds(f"u_{i}", float(capacity))
            
        for i in range(n_locations):
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=[f"x_{i}_{i}"], val=[1.0])],
                senses=["E"],
                rhs=[0.0]
            )
            
        for j in range(1, n_locations):
            ind = [f"x_{i}_{j}" for i in range(n_locations)]
            val = [1.0] * n_locations
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=ind, val=val)],
                senses=["E"],
                rhs=[1.0]
            )
            
        for i in range(1, n_locations):
            ind = [f"x_{i}_{j}" for j in range(n_locations)]
            val = [1.0] * n_locations
            c.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=ind, val=val)],
                senses=["E"],
                rhs=[1.0]
            )
            
        ind = [f"x_0_{j}" for j in range(1, n_locations)]
        val = [1.0] * (n_locations - 1)
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=ind, val=val)],
            senses=["L"],
            rhs=[float(n_fleet)]
        )
        
        ind = [f"x_{i}_0" for i in range(1, n_locations)]
        val = [1.0] * (n_locations - 1)
        c.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=ind, val=val)],
            senses=["L"],
            rhs=[float(n_fleet)]
        )
        
        for i in range(1, n_locations):
            for j in range(1, n_locations):
                if i != j:
                    ind = [f"u_{i}", f"u_{j}", f"x_{i}_{j}"]
                    val = [1.0, -1.0, float(capacity)]
                    c.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=ind, val=val)],
                        senses=["L"],
                        rhs=[float(capacity - demands[j])]
                    )
                    
        solve_start = time.perf_counter()
        c.solve()
        solve_end = time.perf_counter()
        
        status = c.solution.get_status_string()
        
        if "optimal" in status.lower() or "feasible" in status.lower():
            try:
                return c.solution.get_objective_value(), (solve_end - solve_start), f"Success ({status})"
            except cplex.exceptions.CplexSolverError:
                return None, None, f"CPLEX Error: {status}"
        else:
            return None, None, f"CPLEX status: {status}"
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
