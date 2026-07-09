# Instructions for AI Agents in this Workspace

Welcome! This workspace is dedicated to onboarding and instructing AI agents on how to model, solve, and benchmark optimization problems using **NVIDIA cuOpt** on the remote server `orlab`.

## 1. Primary Objectives (Using cuOpt)
Your main tasks in this repository are:
*   **Implement Optimization Models:** Model routing, scheduling, LP, QP, and MIP problems using the cuOpt Python API.
*   **Run Benchmarks on the Remote Server:** Connect via SSH to the remote machine `orlab` (`ssh orlab`), synchronize the codebase, install necessary packages (like `cuopt`, `cudf`, `gurobipy`, `cplex`, `pulp`), and execute the optimization.
*   **Compare Performance:** Run head-to-head benchmarks comparing cuOpt (GPU heuristics) with commercial CPU solvers (Gurobi and CPLEX) on larger datasets (e.g. 100+ node instances) to demonstrate GPU acceleration and quality scaling.
*   **Hybrid Workflows:** Integrate cuOpt as a warm-start generator (MIP start) or subproblem solver in larger mathematical decomposition architectures.

## 2. Slides and Presentation Workflow (Secondary Tasks)
When modifying or updating the presentation slides, you must follow this sequential workflow:

1.  **Update the Markdown Slides First:**
    Always modify the Marp-compatible markdown file [docs/presentation/slides.md](docs/presentation/slides.md) first. Update the outline, slide contents, text structure, and speaker metadata here.

2.  **Synchronize the LaTeX Beamer Document:**
    Replicate the modifications into the LaTeX Beamer file [docs/presentation/slides.tex](docs/presentation/slides.tex) to ensure both file types stay perfectly in sync.

3.  **Recompile the Slide Deck:**
    Run the compilation build command from the terminal in the root directory:
    ```bash
    make
    ```
    This will execute the `pdflatex` build process on `slides.tex` and regenerate the compiled PDF document [docs/presentation/slides.pdf](docs/presentation/slides.pdf).

4.  **Verify and Push Changes:**
    Commit the source changes and the rebuilt PDF, then push to the remote repository. Do not track intermediate build outputs (such as `.aux`, `.log`, `.nav`, etc.) which are ignored via `.gitignore`.
