# Bounded-Suboptimal Search Reference Bibliography

This directory hosts the primary research literature and reference proposals that form the mathematical, algorithmic, and experimental foundations of this benchmarking framework.

---

## 📚 Indexed Reference Library

The reference papers are indexed chronologically and by topic sequence:

### [0_probabilistic_focal_search.md](0_probabilistic_focal_search.md)
*   **Title:** Probabilistic Focal Search: A Simple but Effective Focal Search Variant
*   **Role in Project:** Proposes the core algorithm **PFS** evaluated in this framework, showing that probabilistically alternating between expanding the best state in `FOCAL` and the best state in `OPEN` accelerates lower-bound growth and improves overall runtime.
*   **Key Math:** 
    *   Suboptimality-bounded FOCAL: $FOCAL = \{n \in OPEN : f(n) \le w \cdot f_{\min}\}$
    *   Frontier expansion selection probability: $p \in [0, 1]$

### [1_anytime_focal_search.md](1_anytime_focal_search.md)
*   **Title:** Anytime Focal Search with Applications
*   **Role in Project:** Extends Focal Search to the anytime domain (**AFS**), allowing it to find initial suboptimal solutions rapidly and iteratively refine them as deliberation time permits by reusing prior search effort.

### [2_exploiting_learned_policies_in_focal_search.md](2_exploiting_learned_policies_in_focal_search.md)
*   **Title:** Exploiting Learned Policies in Focal Search
*   **Authors:** Pablo Araneda, Matias Greco, Jorge A. Baier
*   **Role in Project:** Introduces advanced policy-guided Focal Search variants (e.g. *Discrepancy Focal Search*), demonstrating how modern neural-network policy classifiers can be integrated into the secondary selection heuristic while maintaining suboptimality bounds.
*   **Baseline Mentioned:** Focuses on the N-Puzzle (N-Puzzle) and Pancake Sorting domain using Helmert's Gap Heuristic.

### [3_dynamic_potential_search.md](3_dynamic_potential_search.md)
*   **Title:** Dynamic Potential Search: A New Bounded Suboptimal Search Algorithm
*   **Authors:** Daniel Gilon, Ariel Felner, Roni Stern
*   **Role in Project:** Proposes **DPS**, a state-of-the-art bounded-suboptimal search algorithm that eliminates the `FOCAL` threshold altogether by expanding the node that maximizes the probability of finding a solution within the suboptimality budget.
*   **Key Math:**
    *   Dynamic Potential: $u_d(n) = \frac{B \cdot f_{\min} - g(n)}{h(n)}$

### [4_landmark_heuristics_for_the_pancake_problem.md](4_landmark_heuristics_for_the_pancake_problem.md)
*   **Title:** Landmark Heuristics for the Pancake Problem
*   **Author:** Malte Helmert (SoCS 2010)
*   **Role in Project:** Proposes the **Gap Heuristic** ($h_{\text{gap}}$) for the Pancake Sorting puzzle, proving its consistency and admissibility, and demonstrating how delete-relaxation landmarks in STRIPS classical planning explain its phenomenal empirical performance.
*   **Key Math:**
    *   Gap Count: $h_{\text{gap}}(s) := \left| \left\{ i \in \{1, \ldots, n\} \;\middle|\; |s_i - s_{i+1}| > 1 \right\} \right|$

### [5_generalized_covering_tsp.md](5_generalized_covering_tsp.md)
*   **Title:** The Generalized Covering Traveling Salesman Problem
*   **Authors:** Mohammad H. Shaelaie, Majid Salari, Zahra Naji-Azimi (2014)
*   **Role in Project:** Formulates the mathematical models (node-based, flow-based) and metaheuristic algorithms (memetic algorithm, variable neighborhood search) for the GCTSP (Generalized Covering Traveling Salesman Problem), which serves as a benchmark problem in this framework.

### [6_thayer2011_bounded_suboptimal_search_direct_approach.md](6_thayer2011_bounded_suboptimal_search_direct_approach.md)
*   **Title:** Bounded Suboptimal Search: A Direct Approach Using Inadmissible Estimates
*   **Authors:** Jordan T. Thayer and Wheeler Ruml (2011)
*   **Role in Project:** Details **Explicit Estimation Search (EES)**, which separates the role of heuristic search guidance (using inadmissible estimates) and suboptimality bounding (using admissible estimates).


