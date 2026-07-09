# GCTSP Solver Workspace (NVIDIA cuOpt vs. MILP)

This directory contains the Python implementations for solving the **Generalized Covering Traveling Salesman Problem (GCTSP)** using two different paradigms:
1.  **Method A (Direct MILP Formulation):** Formulates GCTSP as a mixed-integer linear program with subtour elimination and solves it using commercial/open-source solvers.
2.  **Method B (Hybrid VRP Decomposition):** Selects a subset of facilities using a set-covering heuristic, sequences the routing tour via **NVIDIA cuOpt** on GPU, and refines the selection via a local search neighborhood.

---

## 1. Directory Structure

*   `parser.py`: Parses `.gctsp` files and computes distance matrices (supporting Euclidean, Geographic, and ATT distance functions).
*   `solve_mip.py`: Formulates and solves the GCTSP model via PuLP using CBC, Gurobi, or CPLEX backends.
*   `solve_hybrid.py`: Formulates and solves the GCTSP model using a greedy set-cover heuristic + local search refinement with `cuopt.routing`.
*   `benchmark.py`: Runs a comparative sweep across the benchmark instances.

---

## 2. How to Run Benchmarks

To run the comparative benchmarks on the `orlab` server, execute:

```bash
# Run small instances using CBC open-source solver
python3 -m sample_project.gctsp.benchmark --folder tsplib_small --solver cbc --max-files 5

# Run medium instances using Gurobi solver
python3 -m sample_project.gctsp.benchmark --folder tsplib_medium --solver gurobi --max-files 10
```

---

## 3. Mathematical Model details

For formulation detail, see the project documentation:
[gctsp_implementation_plan.md](../../gctsp_implementation_plan.md)
