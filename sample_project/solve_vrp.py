import numpy as np

try:
    import cudf
    from cuopt import routing
    HAS_CUOPT = True
except ImportError:
    HAS_CUOPT = False

def solve_with_cuopt():
    print("--- Solving VRP with NVIDIA cuOpt ---")
    
    # 1. Define the Locations and Distance Matrix (4x4)
    # Node 0: Warehouse (Depot)
    # Node 1: Store A
    # Node 2: Store B
    # Node 3: Store C
    distance_data = np.array([
        [0.0, 10.0, 15.0, 20.0],  # From Depot (0)
        [10.0, 0.0, 35.0, 25.0],  # From Store A (1)
        [15.0, 35.0, 0.0, 30.0],  # From Store B (2)
        [20.0, 25.0, 30.0, 0.0]   # From Store C (3)
    ], dtype=np.float32)
    
    # cuOpt requires a GPU DataFrame for the cost matrix
    cost_matrix = cudf.DataFrame(distance_data)
    
    # 2. Initialize the DataModel
    # n_locations = 4 (1 depot + 3 stores)
    # n_fleet = 2 (2 trucks)
    # n_orders = 3 (3 store deliveries)
    dm = routing.DataModel(n_locations=4, n_fleet=2, n_orders=3)
    
    # Add cost matrix
    dm.add_cost_matrix(cost_matrix)
    
    # Set the order locations (Store A, Store B, Store C are at indices 1, 2, 3)
    order_locations = cudf.Series([1, 2, 3], dtype=np.int32)
    dm.set_order_locations(order_locations)
    
    # 3. Add Capacity Constraints
    # Store demands: Store A = 15, Store B = 30, Store C = 20 units
    order_demands = cudf.Series([15, 30, 20], dtype=np.int32)
    # Truck capacities: Each of the 2 trucks can hold up to 40 units
    truck_capacities = cudf.Series([40, 40], dtype=np.int32)
    
    dm.add_capacity_dimension("demand", order_demands, truck_capacities)
    
    # 4. Set start/end locations for the fleet (all trucks start and end at the Depot: index 0)
    truck_starts = cudf.Series([0, 0], dtype=np.int32)
    truck_ends = cudf.Series([0, 0], dtype=np.int32)
    dm.set_vehicle_locations(truck_starts, truck_ends)
    
    # 5. Solver Settings & Execution
    settings = routing.SolverSettings()
    settings.set_time_limit(5) # Set 5-second limit
    
    print("Sending optimization problem to GPU solver...")
    solution = routing.Solve(dm, settings)
    
    # 6. Process the Output
    status = solution.get_status()
    if status == 0:
        print("\n[SUCCESS] Solution Found!")
        print(f"Total travel cost: {solution.get_total_objective():.2f}")
        print("\nRoutes:")
        solution.display_routes()
    else:
        print(f"\n[ERROR] Solver failed with status: {status}")
        print(f"Details: {solution.get_error_message()}")

if __name__ == "__main__":
    if not HAS_CUOPT:
        print("[WARNING] NVIDIA cuOpt and RAPIDS cuDF could not be imported.")
        print("This script requires an NVIDIA GPU, CUDA, and the cuOpt libraries installed.")
        print("To run this code, please upload it to Google Colab (with a GPU runtime) or run it inside an NGC cuOpt Docker container.")
        print("\nExiting. See sample_project/README.md for execution options.")
    else:
        solve_with_cuopt()
