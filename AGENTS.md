# Instructions for AI Agents in this Workspace

Welcome! This workspace is dedicated to onboarding and instructing AI agents on how to model, solve, and benchmark optimization problems using **NVIDIA cuOpt** on the remote server `orlab`.

## 1. Primary Objectives (Using cuOpt)
Your main tasks in this repository are:
*   **Implement Optimization Models:** Model routing, scheduling, LP, QP, and MIP problems using the cuOpt Python API.
*   **Run Benchmarks on the Remote Server:** Connect via SSH to the remote machine `orlab` (`ssh orlab`), synchronize the codebase, install necessary packages (like `cuopt`, `cudf`, `gurobipy`, `cplex`, `pulp`), and execute the optimization.
*   **Compare Performance:** Run head-to-head benchmarks comparing cuOpt (GPU heuristics) with commercial CPU solvers (Gurobi and CPLEX) on larger datasets (e.g. 100+ node instances) to demonstrate GPU acceleration and quality scaling.
*   **Hybrid Workflows:** Integrate cuOpt as a warm-start generator (MIP start) or subproblem solver in larger mathematical decomposition architectures.
