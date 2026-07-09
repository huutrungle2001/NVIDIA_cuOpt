# NVIDIA cuOpt Optimization & Agent Onboarding Hub

Welcome to the NVIDIA cuOpt Optimization Hub. The overarching purpose of this project is to serve as an execution-ready workspace dedicated to **onboarding AI agents**, instructing them on **how to use NVIDIA cuOpt**, and running optimization jobs directly on the remote GPU server `orlab`.

Rather than just reading about optimization, this repository is a functional playground where AI agents model, execute, and benchmark real-world routing and scheduling problems using Gurobi, CPLEX, and cuOpt.

---

## 1. Core Structure & Directories

*   [**docs/**](docs/): Contains all core reference documents, technical overview papers, and the slide deck presentation.
    *   [**00. Executive Summary**](docs/00_summary.md): Concise overview of cuOpt capabilities.
    *   [**01. Overview & Core Capabilities**](docs/01_overview.md): Technical breakdown of the solvers (LP, MIP, VRP, QP) and agent skills.
    *   [**02. Key Benefits**](docs/02_benefits.md): Performance benchmarks, world records, and enterprise support.
    *   [**03. Real-World Use Cases**](docs/03_use_cases.md): Supply chain, fleet management, scheduling, and finance applications.
    *   [**04. Getting Started Guide**](docs/04_getting_started.md): Installation and API setup paths.
    *   [**05. Agentic Workflows & cuOpt Agent Skills**](docs/05_agentic_workflows.md): Instructions for LLM integration.
*   [**docs/presentation/**](docs/presentation/): Directory containing presentation slides and materials.
    *   [**slides.md**](docs/presentation/slides.md): Marp-compatible markdown slide deck.
    *   [**slides.tex**](docs/presentation/slides.tex): LaTeX Beamer version of the slide deck.
    *   [**slides.pdf**](docs/presentation/slides.pdf): Pre-compiled presentation slide deck PDF.
*   [**sample_project/**](sample_project/): Functional Python implementations of optimization solvers.
    *   [**solve_vrp.py**](sample_project/solve_vrp.py): Simple Capacitated Vehicle Routing Problem (CVRP) model solved via cuOpt.
    *   [**solve_benchmark.py**](sample_project/solve_benchmark.py): Parallel VRP benchmark comparing cuOpt, Gurobi, and CPLEX.
    *   [**solve_hybrid_cuopt.py**](sample_project/solve_hybrid_cuopt.py): Multi-modal Truck-Drone Hybrid Routing problem using cuOpt's heterogeneous fleet capabilities.
    *   [**warm_start_tsp.py**](sample_project/warm_start_tsp.py): Hybrid warm-start optimization using cuOpt to generate MIP Starts for Gurobi.

---

## 2. Onboarding AI Agents (Instruction Files)

All AI agents arriving in this workspace should immediately read:
*   [**AGENTS.md**](AGENTS.md) / [**.agents/AGENTS.md**](.agents/AGENTS.md): Detailed workflow instructions for agents. This outlines slide synchronization rules, remote server compilation scripts, and primary/secondary coding objectives.

---

## 3. Remote Server Compilation & Run Commands

A root `Makefile` is provided to easily rebuild slides and clean artifacts:
```bash
# Rebuild the LaTeX slide deck presentation PDF
make slides

# Clean temporary compilation trash files (.aux, .log, .nav, etc.)
make clean
```
