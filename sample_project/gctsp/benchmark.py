import os
import sys
import glob
import argparse
import pandas as pd
from sample_project.gctsp.solve_mip import solve_gctsp_mip
from sample_project.gctsp.solve_hybrid import solve_gctsp_hybrid

def run_benchmarks(folder_name="tsplib_small", solver_name="cbc", max_files=5):
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
    print(f"Benchmarking {len(files)} files from {folder_name} using MIP solver: {solver_name}...")
    
    results = []
    
    for f in files:
        basename = os.path.basename(f)
        print(f"\n--- Running instance: {basename} ---")
        
        # Run Method A: MIP
        try:
            res_mip = solve_gctsp_mip(f, solver_name=solver_name, time_limit=30)
        except Exception as e:
            res_mip = {'status': f"ERROR ({str(e)})", 'objective': None, 'time_s': 0.0}
            
        # Run Method B: Hybrid cuOpt
        try:
            res_hybrid = solve_gctsp_hybrid(f, max_iterations=500)
        except Exception as e:
            res_hybrid = {'status': f"ERROR ({str(e)})", 'objective': None, 'time_s': 0.0}
            
        # Compute gap
        gap = None
        if res_mip['objective'] is not None and res_hybrid['objective'] is not None and res_mip['objective'] > 0:
            gap = ((res_hybrid['objective'] - res_mip['objective']) / res_mip['objective']) * 100
            
        results.append({
            'Instance': basename,
            'MIP Status': res_mip['status'],
            'MIP Cost': f"{res_mip['objective']:.2f}" if res_mip['objective'] is not None else "N/A",
            'MIP Time (s)': f"{res_mip['time_s']:.3f}",
            'Hybrid Status': res_hybrid['status'],
            'Hybrid Cost': f"{res_hybrid['objective']:.2f}" if res_hybrid['objective'] is not None else "N/A",
            'Hybrid Time (s)': f"{res_hybrid['time_s']:.3f}",
            'Gap (%)': f"{gap:.2f}%" if gap is not None else "N/A"
        })
        
    df = pd.DataFrame(results)
    
    print("\n================================ BENCHMARK RESULTS ================================")
    print(df.to_markdown(index=False))
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
    
    args = parser.parse_args()
    run_benchmarks(folder_name=args.folder, solver_name=args.solver, max_files=args.max_files)
