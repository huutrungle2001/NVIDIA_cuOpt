# NVIDIA cuOpt: Agentic Workflows & Agent Skills

In modern AI architectures, decision optimization is no longer isolated to static codebases. Instead, **AI Agents** (large language models equipped with tool execution capabilities) are deployed to dynamically formulate, solve, and adapt optimization models. 

To enable this, NVIDIA provides **cuOpt Agent Skills**—modular, pre-verified instruction sets and code patterns that teach AI agents how to interact with the cuOpt optimization engine.

---

## 1. What are Agentic Workflows?

An **Agentic Workflow** is a multi-step execution loop where an AI agent:
1.  **Ingests** natural language business goals (e.g., *"We need to reroute our delivery vans because a bridge closed on Route 9"*).
2.  **Clarifies** missing details by asking structured questions about fleet sizes, capacities, and time windows.
3.  **Formulates** the mathematical model (using explicit constraints).
4.  **Executes** the solver (calling cuOpt APIs).
5.  **Debugs** infeasibilities (interpreting solver status codes and adjusting parameters).
6.  **Translates** the raw route tables back into clear, natural language recommendations.

---

## 2. Core cuOpt Agent Skills

In the `NVIDIA/skills` repository, the cuOpt division is split into specialized task skills:

### A. Problem Formulation Skills
*   **`cuopt-routing-formulation`:** Teaches agents how to categorize routing problems into:
    *   *Traveling Salesperson (TSP):* Single vehicle, complete tour.
    *   *Vehicle Routing Problem (VRP):* Multiple vehicles with capacities and/or time windows.
    *   *Pickup and Delivery Problem (PDP):* Interdependent pickup/delivery node pairs.
*   **`cuopt-numerical-optimization-formulation`:** Focuses on framing general mathematical constraints (Linear Programming, Mixed-Integer, Quadratic) from raw text.

### B. Python API Implementation Skills
*   **`cuopt-routing-api-python`:** Instructs agents on writing valid `cudf` (GPU DataFrame) and `cuopt.routing` code:
    *   Initializing the `DataModel` with explicit locations and fleet bounds.
    *   Adding cost matrices and capacity dimensions with correct GPU data types (`float32` and `int32`).
    *   Running the solver: `solution = routing.Solve(dm, solver_settings)`.
    *   Retrieving route mappings: `solution.get_route()`.
*   **`cuopt-numerical-optimization-api-python`:** Teaches agents how to interface cuOpt with high-level packages (CVXPY, Gurobi, JuMP, AMPL) for numerical models.

---

## 3. Step-by-Step Agent Execution Example

Here is a typical workflow demonstrating how an AI agent executes these skills:

### Step 1: Input Ingestion & Inquiries
*   *User request:* "Create a schedule to deliver supplies from our main warehouse (depot 0) to stores 1, 2, and 3 using our two trucks."
*   *Agent's Internal Action:* The agent triggers `cuopt-routing-formulation` and identifies it as a VRP. It notices travel times and truck capacities are missing, prompting:
    > "Could you please specify the load capacity of each truck, and the travel times or distances between these locations?"

### Step 2: Code Formulation
*   *User replies:* "Each truck holds 50 units. The distance matrix is `[[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]`. Order demands are: Store 1 = 20, Store 2 = 40, Store 3 = 10 units."
*   *Agent's Internal Action:* Triggers `cuopt-routing-api-python` to write the execution script:
    ```python
    import cudf
    import numpy as np
    from cuopt import routing

    # Setup the distance matrix
    distances = np.array([[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]], dtype=np.float32)
    cost_matrix = cudf.DataFrame(distances)

    # Initialize model: 4 locations (including depot), 2 vehicles, 3 orders
    dm = routing.DataModel(n_locations=4, n_fleet=2, n_orders=3)
    dm.add_cost_matrix(cost_matrix)
    dm.set_order_locations(cudf.Series([1, 2, 3], dtype=np.int32))

    # Add capacity constraint (weight)
    demands = cudf.Series([20, 40, 10], dtype=np.int32)
    capacities = cudf.Series([50, 50], dtype=np.int32)
    dm.add_capacity_dimension("weight", demands, capacities)

    # Solve VRP
    solver_settings = routing.SolverSettings()
    solution = routing.Solve(dm, solver_settings)
    ```

### Step 3: Debugging & Execution
*   If the solution status code returns `1` (Infeasible) or `3` (Empty), the agent references the *Common Issues* table in the skill card:
    *   *Issue:* Total order demand (20 + 40 + 10 = 70 units) exceeds total fleet capacity (50 + 50 = 100 units)? No, total capacity is sufficient, but individual capacity (50) means one truck cannot carry Store 1 + Store 2 (20 + 40 = 60). Therefore, the route must split Store 2 onto its own truck.
    *   *Status:* If the solver shows an error, the agent runs `solution.get_infeasible_orders()` to isolate the bottleneck and explains it to the user.

---

## 4. Trust & Security: Skill Cards

For enterprise safety, each skill is defined by a **Skill Card** (`skill-card.md`):
*   **Verification:** Signals whether the skill has been audited by NVIDIA security teams.
*   **Version Pinning:** Restricts the code template to compatible cuOpt releases (e.g., `26.08.00`).
*   **Boundary Constraints:** Specifies the exact mathematical limits of the skill to prevent halluncinations.

---

*Related Documents:*
- [**00. Executive Summary**](./00_summary.md)
- [**01. Overview & Core Capabilities**](./01_overview.md)
- [**02. Key Benefits**](./02_benefits.md)
- [**03. Use Cases**](./03_use_cases.md)
- [**04. Getting Started**](./04_getting_started.md)
- [**README Index**](./README.md)
