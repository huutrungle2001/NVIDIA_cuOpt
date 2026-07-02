import sys
import time
import numpy as np

try:
    import cudf
    from cuopt import routing
    HAS_CUOPT = True
except ImportError:
    HAS_CUOPT = False

def parse_instance(filepath):
    num_drones = 4
    num_trucks = 10
    truck_capacity = 1300.0
    drone_capacity = 2.27
    truck_speed = 30.0
    drone_speed = 40.0
    
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
            if key == "NUM DRONES":
                num_drones = int(val)
            elif key == "NUM TRUCKS":
                num_trucks = int(val)
            elif key == "TRUCK CAP":
                truck_capacity = float(val)
            elif key == "DRONE CAP":
                drone_capacity = float(val)
            elif key == "TRUCK SPEED":
                truck_speed = float(val)
            elif key == "DRONE SPEED":
                drone_speed = float(val)
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
                
    return num_drones, num_trucks, truck_capacity, drone_capacity, truck_speed, drone_speed, coords, demands

def calculate_distance_matrix(coords):
    n = len(coords)
    matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            matrix[i][j] = np.sqrt(dx*dx + dy*dy)
    return matrix

def solve_hybrid_with_cuopt(filepath, limit):
    if not HAS_CUOPT:
        print("[ERROR] cuOpt is not installed in this environment.")
        return
        
    print(f"Parsing instance file: {filepath}...")
    num_drones, num_trucks, truck_cap, drone_cap, truck_speed, drone_speed, coords, demands = parse_instance(filepath)
    n_locations = len(coords)
    
    print(f"Loaded {n_locations} locations (depot + {n_locations-1} customers).")
    print(f"Truck fleet: {num_trucks} trucks (Speed={truck_speed}, Capacity={truck_cap})")
    print(f"Drone fleet: {num_drones} drones (Speed={drone_speed}, Capacity={drone_cap})")
    
    distances = calculate_distance_matrix(coords)
    truck_time_matrix = (distances / truck_speed) * 3600.0
    drone_time_matrix = (distances / drone_speed) * 3600.0
    
    truck_df = cudf.DataFrame(truck_time_matrix)
    drone_df = cudf.DataFrame(drone_time_matrix)
    
    n_fleet = num_trucks + num_drones
    n_orders = n_locations - 1
    dm = routing.DataModel(n_locations=n_locations, n_fleet=n_fleet, n_orders=n_orders)
    
    dm.add_cost_matrix(truck_df, 0)
    dm.add_cost_matrix(drone_df, 1)
        
    vehicle_types = cudf.Series([0] * num_trucks + [1] * num_drones, dtype=np.int32)
    dm.set_vehicle_types(vehicle_types)
        
    dm.set_order_locations(cudf.Series(range(1, n_locations), dtype=np.int32))
    
    order_demands_weight = cudf.Series((np.array(demands[1:]) * 100.0).astype(np.int32))
    vehicle_capacities_weight = cudf.Series([int(truck_cap * 100)] * num_trucks + [int(drone_cap * 100)] * num_drones, dtype=np.int32)
    dm.add_capacity_dimension("weight", order_demands_weight, vehicle_capacities_weight)
    
    order_demands_package = cudf.Series([1] * n_orders, dtype=np.int32)
    vehicle_capacities_package = cudf.Series([999] * num_trucks + [1] * num_drones, dtype=np.int32)
    dm.add_capacity_dimension("packages", order_demands_package, vehicle_capacities_package)
    
    vehicle_starts = cudf.Series([0] * n_fleet, dtype=np.int32)
    vehicle_ends = cudf.Series([0] * n_fleet, dtype=np.int32)
    dm.set_vehicle_locations(vehicle_starts, vehicle_ends)
    
    settings = routing.SolverSettings()
    settings.set_time_limit(limit)
    settings.set_verbose_mode(False)
    
    print(f"\nSolving Truck-Drone VRP with cuOpt (Time Limit = {limit}s)...")
    solve_start = time.perf_counter()
    solution = routing.Solve(dm, settings)
    solve_end = time.perf_counter()
    
    status = solution.get_status()
    if status == 0:
        print("\n[SUCCESS] cuOpt Routing Solution Found!")
        solve_duration = solve_end - solve_start
        print(f"GPU Solve time: {solve_duration * 1000:.2f} ms")
        
        route_df = solution.get_route()
        
        vehicle_times = []
        for v in range(n_fleet):
            v_route = route_df[route_df['route'] == v]
            if not v_route.empty:
                nodes = v_route['location'].to_arrow().to_pylist()
                total_time = 0.0
                curr = 0
                for node in nodes:
                    if v < num_trucks:
                        total_time += truck_time_matrix[curr][node]
                    else:
                        total_time += drone_time_matrix[curr][node]
                    curr = node
                if v < num_trucks:
                    total_time += truck_time_matrix[curr][0]
                else:
                    total_time += drone_time_matrix[curr][0]
                
                vehicle_times.append(total_time)
                v_name = f"Truck {v}" if v < num_trucks else f"Drone {v - num_trucks}"
                print(f"  - {v_name} time: {total_time:.2f} seconds ({total_time / 60.0:.2f} minutes)")
            else:
                v_name = f"Truck {v}" if v < num_trucks else f"Drone {v - num_trucks}"
                print(f"  - {v_name} idle")
                
        truck_times = vehicle_times[:num_trucks]
        drone_times = vehicle_times[num_trucks:]
        
        max_truck_time = max(truck_times) if len(truck_times) > 0 else 0
        max_drone_time = max(drone_times) if len(drone_times) > 0 else 0
        makespan = max(max_truck_time, max_drone_time)
        
        print("\n==================================================")
        print(f"cuOpt Makespan (max time): {makespan:.2f} seconds ({makespan / 60.0:.2f} minutes)")
        print("==================================================")
    else:
        print(f"\n[ERROR] cuOpt solver failed: {solution.get_error_message()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solve_hybrid_cuopt.py <instance_file> [time_limit_seconds]")
        sys.exit(1)
        
    filepath = sys.argv[1]
    time_limit = 10
    if len(sys.argv) >= 3:
        time_limit = int(sys.argv[2])
        
    solve_hybrid_with_cuopt(filepath, time_limit)
