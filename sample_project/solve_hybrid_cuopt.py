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
    # Default values
    num_drones = 4
    num_trucks = 1  # We only model 1 truck active in this parallel problem
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
                
    return num_drones, truck_capacity, drone_capacity, truck_speed, drone_speed, coords, demands

def calculate_distance_matrix(coords):
    n = len(coords)
    matrix = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            matrix[i][j] = np.sqrt(dx*dx + dy*dy)
    return matrix

def solve_hybrid_with_cuopt(filepath):
    if not HAS_CUOPT:
        print("[ERROR] cuOpt is not installed in this environment.")
        return
        
    print(f"Parsing instance file: {filepath}...")
    num_drones, truck_cap, drone_cap, truck_speed, drone_speed, coords, demands = parse_instance(filepath)
    n_locations = len(coords)
    
    print(f"Loaded {n_locations} locations (depot + {n_locations-1} customers).")
    print(f"Truck fleet: 1 truck (Speed={truck_speed}, Capacity={truck_cap})")
    print(f"Drone fleet: {num_drones} drones (Speed={drone_speed}, Capacity={drone_cap})")
    
    # 1. Compute Distance Matrix (in miles or km)
    distances = calculate_distance_matrix(coords)
    
    # 2. Compute Travel Time Matrices in hours (Distance / Speed)
    # Gurobi C++ solver uses seconds or hours. Let's make sure our time matches seconds.
    # From data: speed is given, coordinate units and time are matched.
    # In the C++ solver, distances are in miles, speed in miles/hour. 
    # Time is converted to seconds: time_seconds = (distance / speed) * 3600.
    truck_time_matrix = (distances / truck_speed) * 3600.0
    drone_time_matrix = (distances / drone_speed) * 3600.0
    
    # cuOpt requires GPU DataFrames for the cost matrices
    truck_df = cudf.DataFrame(truck_time_matrix)
    drone_df = cudf.DataFrame(drone_time_matrix)
    
    # Initialize the DataModel: 1 truck + num_drones vehicles
    n_fleet = 1 + num_drones
    n_orders = n_locations - 1
    dm = routing.DataModel(n_locations=n_locations, n_fleet=n_fleet, n_orders=n_orders)
    
    # Add heterogeneous cost matrices: 
    # Vehicle 0 is the Truck, Vehicles 1 to N are the Drones
    dm.add_cost_matrix(truck_df, 0)
    for i in range(1, n_fleet):
        dm.add_cost_matrix(drone_df, i)
        
    dm.set_order_locations(cudf.Series(range(1, n_locations), dtype=np.int32))
    
    # Define Dimensions:
    # Dimension 1: Cargo weight (Truck cap = truck_cap, Drone cap = drone_cap)
    order_demands_weight = cudf.Series(demands[1:], dtype=np.float32)
    vehicle_capacities_weight = cudf.Series([truck_cap] + [drone_cap] * num_drones, dtype=np.float32)
    dm.add_capacity_dimension("weight", order_demands_weight, vehicle_capacities_weight)
    
    # Dimension 2: Package count (Truck cap = unlimited, Drone cap = 1 to force return after each customer)
    order_demands_package = cudf.Series([1] * n_orders, dtype=np.int32)
    vehicle_capacities_package = cudf.Series([999] + [1] * num_drones, dtype=np.int32)
    dm.add_capacity_dimension("packages", order_demands_package, vehicle_capacities_package)
    
    # All vehicles start and end at the Depot (Node 0)
    vehicle_starts = cudf.Series([0] * n_fleet, dtype=np.int32)
    vehicle_ends = cudf.Series([0] * n_fleet, dtype=np.int32)
    dm.set_vehicle_locations(vehicle_starts, vehicle_ends)
    
    # Solve settings
    settings = routing.SolverSettings()
    settings.set_time_limit(10)
    settings.set_verbose_mode(False)
    
    print("\nSolving Truck-Drone VRP with cuOpt...")
    solve_start = time.perf_counter()
    solution = routing.Solve(dm, settings)
    solve_end = time.perf_counter()
    
    status = solution.get_status()
    if status == 0:
        print("\n[SUCCESS] cuOpt Routing Solution Found!")
        solve_duration = solve_end - solve_start
        print(f"GPU Solve time: {solve_duration * 1000:.2f} ms")
        
        # Get route details and calculate makespan
        route_df = solution.get_route()
        
        # Parse individual vehicle times
        vehicle_times = []
        for v in range(n_fleet):
            v_route = route_df[route_df['route'] == v]
            if not v_route.empty:
                # Total time for vehicle is the arrival time of its last return to the depot
                # Gurobi/cuOpt objective uses the cost matrix. 
                # Let's compute the total path duration manually from the cost matrix:
                nodes = v_route['location'].to_list()
                total_time = 0.0
                curr = 0
                for node in nodes:
                    if v == 0:
                        total_time += truck_time_matrix[curr][node]
                    else:
                        total_time += drone_time_matrix[curr][node]
                    curr = node
                # Return back to depot
                if v == 0:
                    total_time += truck_time_matrix[curr][0]
                else:
                    total_time += drone_time_matrix[curr][0]
                
                vehicle_times.append(total_time)
                v_name = "Truck" if v == 0 else f"Drone {v-1}"
                print(f"  - {v_name} time: {total_time:.2f} seconds ({total_time / 60.0:.2f} minutes)")
            else:
                v_name = "Truck" if v == 0 else f"Drone {v-1}"
                print(f"  - {v_name} idle")
                
        truck_time = vehicle_times[0] if len(vehicle_times) > 0 else 0
        drone_makespan = max(vehicle_times[1:]) if len(vehicle_times) > 1 else 0
        makespan = max(truck_time, drone_makespan)
        
        print("\n==================================================")
        print(f"cuOpt Makespan (max time): {makespan:.2f} seconds ({makespan / 60.0:.2f} minutes)")
        print("==================================================")
    else:
        print(f"\n[ERROR] cuOpt solver failed: {solution.get_error_message()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python solve_hybrid_cuopt.py <instance_file>")
        sys.exit(1)
        
    solve_hybrid_with_cuopt(sys.argv[1])
