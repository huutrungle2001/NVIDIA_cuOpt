# NVIDIA cuOpt: Overview & Core Capabilities

NVIDIA® cuOpt™ is an open-source, GPU-accelerated engine for decision optimization. It is engineered to solve complex, large-scale mathematical programming and routing problems with millions of variables and constraints in near real-time.

---

## 1. Core Solver Support

NVIDIA cuOpt integrates several solver engines to handle a broad range of mathematical optimization classes:

*   **Linear Programming (LP/PDLP):** Utilizes GPU parallel computation to handle extremely large LP problems, leveraging modern methods like the Primal-Dual Hybrid Gradient (PDLP) algorithm.
*   **Vehicle Routing Problems (VRP):** Specialized for solving complex variations of routing challenges including:
    *   Traveling Salesperson Problem (TSP)
    *   Pickup and Delivery Problem (PDP)
    *   Time windows, driver limits, vehicle capacities, and multiple depots.
*   **Quadratic Programming (QP):** Optimizes quadratic objective functions subject to linear constraints.
*   **Mixed-Integer Linear Programming (MILP/MIP) *[Beta]*:** Accelerates mixed-integer optimization by utilizing GPUs to run primal heuristics. The primary focus of the beta is to find high-quality feasible solutions rapidly.
*   **Advanced Models *[Beta]*:** Includes support for Quadratically Constrained Quadratic Programming (QCQP) and Second-Order Cone Programming (SOCP).

---

## 2. Agentic Workflows & cuOpt Agent Skills

A key differentiator for modern deployments is the integration of cuOpt into AI agent architectures using **NVIDIA-verified Agent Skills**:

*   **Natural Language Translation:** AI agents leverage cuOpt agent skills to translate plain English business rules and operational constraints into mathematical models.
*   **Modular Skills Catalog:** NVIDIA provides open-source, pre-verified skills via the `NVIDIA/skills` GitHub repository, including:
    *   **Customer Allocation Skill:** Determines the optimal distribution of customers to service units.
    *   **Generic Max Supply Skill:** Optimizes resources across supply lines.
    *   **cuOpt Solver Skill:** Interfaces directly with the underlying GPU-accelerated solver engine.
*   **Trust and Governance:** Each skill is accompanied by a **Skill Card**—machine-readable metadata indicating ownership, capabilities, constraints, and validation status to ensure reliable production usage.

---

## 3. GPU-Accelerated Primal Heuristics for MIP

Mixed-Integer Programming is traditionally CPU-bound. cuOpt introduces a **hybrid GPU/CPU paradigm** to optimize execution:

*   **Primal Heuristics on GPU:** Algorithms that hunt for high-quality, feasible integer solutions are offloaded to parallel GPU architectures. This allows cuOpt to explore vast areas of the search space instantly.
*   **Branch-and-Bound on CPU:** Traditional search trees and dual-bound calculations are managed by the CPU, resulting in a collaborative solver framework.
*   **Implemented Heuristics:**
    *   *Feasibility Pump & Feasibility Jump:* Methods to rapidly project fractional LP solutions onto integer coordinates.
    *   *Fix-and-Propagate:* Selectively fixing integer variables and propagating constraints.
    *   *Probing Caches:* Rapidly screening variables to detect infeasibilities early and prune search directions.

---

*Related Documents:*
- [**Executive Summary**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/summary.md)
- [**02. Key Benefits**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/02_benefits.md)
- [**03. Real-World Use Cases**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/03_use_cases.md)
- [**04. Getting Started Guide**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/04_getting_started.md)
- [**README Index**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/README.md)
