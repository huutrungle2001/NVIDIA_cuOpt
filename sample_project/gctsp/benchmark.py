import os
import sys
import glob
import argparse
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from sample_project.gctsp.solve_mip import solve_gctsp_mip
from sample_project.gctsp.solve_hybrid import solve_gctsp_hybrid

def solve_single_instance(filepath, solver_name):
    basename = os.path.basename(filepath)
    print(f"Starting instance: {basename}...")
    
    # Run Method A: MIP
    try:
        res_mip = solve_gctsp_mip(filepath, solver_name=solver_name, time_limit=30)
    except Exception as e:
        res_mip = {'status': f"ERROR ({str(e)})", 'objective': None, 'time_s': 0.0}
        
    # Run Method B: Hybrid cuOpt
    try:
        res_hybrid = solve_gctsp_hybrid(filepath, max_iterations=500)
    except Exception as e:
        res_hybrid = {'status': f"ERROR ({str(e)})", 'objective': None, 'time_s': 0.0}
        
    # Compute gap
    gap = None
    if res_mip['objective'] is not None and res_hybrid['objective'] is not None and res_mip['objective'] > 0:
        gap = ((res_hybrid['objective'] - res_mip['objective']) / res_mip['objective']) * 100
        
    return {
        'Instance': basename,
        'MIP Status': res_mip['status'],
        'MIP Cost': f"{res_mip['objective']:.2f}" if res_mip['objective'] is not None else "N/A",
        'MIP Time (s)': f"{res_mip['time_s']:.3f}",
        'Hybrid Status': res_hybrid['status'],
        'Hybrid Cost': f"{res_hybrid['objective']:.2f}" if res_hybrid['objective'] is not None else "N/A",
        'Hybrid Time (s)': f"{res_hybrid['time_s']:.3f}",
        'Gap (%)': f"{gap:.2f}%" if gap is not None else "N/A"
    }

def run_benchmarks(folder_name="tsplib_small", solver_name="cbc", max_files=5, jobs=1):
    base_dir = "/Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/data/gctsp"
    # Fallback to server path if running on server
    if not os.path.exists(base_dir):
        base_dir = "/home/orlab/TrungLeHuu/NVIDIA_cuOpt/data/gctsp"
        
    folder_path = os.path.join(base_dir, folder_name)
    if not os.path.exists(folder_path):
        print(f"[ERROR] Path does not exist: {folder_path}")
        return
        
    files = sorted(glob.glob(os.path.join(folder_path, "*.gctsp")))
    if not files:
        print(f"[WARNING] No .gctsp files found in {folder_path}")
        return
        
    files = files[:max_files]
    print(f"Benchmarking {len(files)} files from {folder_name} (Parallel Jobs = {jobs}, Solver = {solver_name})...")
    
    start_bench = time.perf_counter()
    
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            futures = [executor.submit(solve_single_instance, f, solver_name) for f in files]
            results = [future.result() for future in futures]
    else:
        results = [solve_single_instance(f, solver_name) for f in files]
        
    total_elapsed = time.perf_counter() - start_bench
    
    df = pd.DataFrame(results)
    
    print("\n================================ BENCHMARK RESULTS ================================")
    print(df.to_markdown(index=False))
    print(f"Total benchmark execution time: {total_elapsed:.2f} seconds")
    print("===================================================================================")
    
    # Save results to a CSV
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gctsp")
    df.to_csv(os.path.join(out_dir, "benchmark_results.csv"), index=False)
    print(f"Results saved to {os.path.join(out_dir, 'benchmark_results.csv')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GCTSP comparative benchmarks")
    parser.add_argument("--folder", type=str, default="tsplib_small", help="Dataset folder (tsplib_small, tsplib_medium, tsplib_large)")
    parser.add_argument("--solver", type=str, default="cbc", help="MIP backend solver (cbc, gurobi, cplex)")
    parser.add_argument("--max-files", type=int, default=5, help="Maximum number of files to run")
    parser.add_argument("--jobs", type=int, default=1, help="Number of parallel processes to run")
    
    args = parser.parse_args()
    run_benchmarks(folder_name=args.folder, solver_name=args.solver, max_files=args.max_files, jobs=args.jobs)

