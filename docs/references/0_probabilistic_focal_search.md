# Probabilistic Focal Search: A Simple but Effective Focal Search Variant

## Abstract

Focal Search (FS) is a bounded-suboptimal search framework that extends A* by maintaining a secondary list, called FOCAL, containing all open states whose evaluation values are within a prescribed factor of the current minimum OPEN value. Classical FS always expands the most promising state in FOCAL according to a secondary priority function. In this paper, we introduce Probabilistic Focal Search (PFS), a simple variant that probabilistically alternates between expanding the best state in FOCAL and expanding the best state in OPEN. The motivation is to increase the current lower-bound estimate more actively, thereby enlarging FOCAL earlier and increasing the chance of reaching a bounded-suboptimal goal state quickly. We prove that PFS preserves the standard $w$-suboptimality guarantee under an admissible heuristic. We also discuss how the probability parameter controls the trade-off between focal-driven exploration and lower-bound advancement. The proposed method is evaluated on several standard search domains, including n-puzzle puzzles, the traveling salesman problem, the generalized covering traveling salesman problem, and the pancake problem. The experimental protocol compares PFS with A*, Weighted A*, and classical FS in terms of solution quality, runtime, and number of expanded states.

## Introduction

Many combinatorial optimization and pathfinding problems can be formulated as finding a least-cost path from an initial state to a goal state in an implicit graph. A* search [hart1968formal] is one of the most widely used algorithms for this setting. For each state $n$, A* evaluates

$$
f(n) = g(n) + h(n),
$$

where $g(n)$ is the exact cost of the best currently known path from the initial state to $n$, and $h(n)$ is a heuristic estimate of the remaining cost from $n$ to a goal state. If $h$ is admissible, i.e., it never overestimates the true remaining cost, A* is guaranteed to return an optimal solution.

Despite this guarantee, A* may become computationally expensive on large instances because it must often expand a very large number of states before proving optimality. Bounded-suboptimal search addresses this limitation by allowing the returned solution to be within a user-specified multiplicative factor $w \geq 1$ of the optimal solution cost. Weighted A* [pohl1970heuristic], for example, uses the inflated evaluation function

$$
f_w(n) = g(n) + w h(n)
$$

and greedily expands states with minimum $f_w$ value.

Focal Search (FS) [pearl1982studies] is another classical bounded-suboptimal search framework. Instead of always expanding the state with the smallest $f$ value, FS maintains a set of admissible candidates, called FOCAL, and selects states from this set according to a secondary priority function. In the standard bounded-suboptimal version,

$$
FOCAL = \{n \in OPEN : f(n) \leq w f_{\min}\},
$$

where $f_{\min}$ is the smallest $f$ value among all states in OPEN. If the secondary priority is well designed, FS can find high-quality bounded-suboptimal solutions faster than A*.

However, classical FS always expands states from FOCAL. Consequently, it may spend many iterations exploring states that are promising according to the secondary priority but do not increase $f_{\min}$. Since the threshold $w f_{\min}$ directly controls the size of FOCAL, slow growth of $f_{\min}$ may delay the inclusion of goal-directed states that would otherwise lead to an early feasible solution.

This paper proposes *Probabilistic Focal Search* (PFS), a simple variant of FS. At each iteration, PFS either expands the best state in FOCAL or the best state in OPEN, according to a probability parameter. Expanding from FOCAL exploits the secondary priority, while expanding from OPEN advances the lower-bound frontier. The proposed algorithm is easy to implement, preserves the $w$-suboptimality guarantee, and provides a tunable mechanism for balancing exploitation of the focal list and progression of the search frontier.

The main contributions of this paper are as follows:

1. We introduce PFS, a probabilistic variant of FS that alternates between focal-driven expansion and OPEN-driven expansion.
2. We prove that PFS preserves the standard $w$-suboptimality guarantee when the heuristic is admissible.
3. We analyze the role of the probability parameter and explain how it controls the rate at which the FOCAL threshold grows.
4. We design an experimental protocol for evaluating PFS on several standard search and combinatorial optimization domains.

## Background: Focal Search

Let $OPEN$ denote the set of generated but unexpanded states. Let

$$
f_{\min} = \min_{n \in OPEN} f(n).
$$

In bounded-suboptimal FS, the focal list is defined as

$$
FOCAL = \{n \in OPEN : f(n) \leq w f_{\min}\},
$$

where $w \geq 1$ is the desired suboptimality bound. FS then selects a state from FOCAL using a secondary priority function $d(n)$, such as an estimate of distance-to-go, number of conflicts, or another domain-dependent measure. A typical implementation expands

$$
n = \arg\min_{u \in FOCAL} d(u).
$$

Two common definitions of focal lists are discussed in the literature [cohen2018anytime]:

1. **Suboptimality-bounded FOCAL:** $FOCAL = \{n \in OPEN : f(n) \leq w f_{\min}\}$.
2. **Cost-bounded FOCAL:** $FOCAL = \{n \in OPEN : f(n) \leq C\}$, where $C$ is a fixed cost bound.

This paper focuses on the suboptimality-bounded definition. Under this definition, the threshold $w f_{\min}$ grows when $f_{\min}$ grows. Therefore, advancing the head of OPEN can enlarge FOCAL and may expose additional promising states earlier.

## Probabilistic Focal Search

PFS modifies FS by changing only the state-selection rule. At each iteration, PFS draws a random number $r \in [0,1]$. With probability $p$, it expands the best state in FOCAL according to the secondary priority function. With probability $1-p$, it expands the best state in OPEN according to the primary $f$ value.

The parameter $p$ controls the behavior of the algorithm. When $p=1$, PFS reduces to classical FS. When $p=0$, PFS always expands the state with the smallest $f$ value in OPEN, resembling A* with respect to the primary ordering. Intermediate values of $p$ interpolate between these two behaviors.

Figure 1 illustrates the conceptual difference between FS and PFS. Classical FS repeatedly expands from FOCAL, whereas PFS occasionally expands the head of OPEN to increase $f_{\min}$ and enlarge the FOCAL threshold.

![Conceptual difference between classical Focal Search and Probabilistic Focal Search. PFS occasionally expands the best state in OPEN to advance $f_{\min}$ and enlarge the FOCAL threshold.](references/fps.png)

**Figure 1:** Conceptual difference between classical Focal Search and Probabilistic Focal Search. PFS occasionally expands the best state in OPEN to advance $f_{\min}$ and enlarge the FOCAL threshold.

**Algorithm 1: Probabilistic Focal Search**

**Input:** initial state $s$, goal test $Goal(\cdot)$, suboptimality factor $w \geq 1$, focal probability $p \in [0,1]$  
**Output:** a solution path whose cost is at most $w$ times the optimal cost, or failure

```text
OPEN <- {s}; CLOSED <- empty set
g(s) <- 0; parent(s) <- empty set

while OPEN != empty set:
    f_min <- min_{u in OPEN} f(u)
    FOCAL <- {u in OPEN : f(u) <= w f_min}
    Draw r uniformly at random from [0,1]

    if r <= p:
        n <- argmin_{u in FOCAL} d(u)     # secondary priority
    else:
        n <- argmin_{u in OPEN} f(u)      # primary priority

    if Goal(n):
        return the path reconstructed from parent(.)

    Remove n from OPEN and add it to CLOSED

    for each n' in Succ(n):
        g_hat <- g(n) + c(n,n')

        if n' has not been generated before or g_hat < g(n'):
            g(n') <- g_hat; parent(n') <- n

            if n' in CLOSED:
                Remove n' from CLOSED     # reopening if necessary

            Insert or update n' in OPEN

return failure
```

The algorithm above recomputes FOCAL conceptually at each iteration for clarity. In practice, FOCAL can be updated incrementally, as in standard FS implementations, by inserting states whose $f$ values newly satisfy the condition $f(n) \leq w f_{\min}$ when $f_{\min}$ increases.

## Theoretical Properties

We first show that PFS preserves the usual bounded-suboptimality guarantee of FS.

**Assumption 1.** The heuristic $h$ is admissible, all edge costs are nonnegative, and $h(n)=0$ for every goal state $n$.

**Theorem 1.** If PFS terminates by returning a goal state, then the cost of the returned solution is at most $w$ times the optimal solution cost.

**Proof.** Let $C^*$ be the optimal solution cost. Since $h$ is admissible, for every state $u \in OPEN$, $f(u)$ is a lower bound on the cost of an optimal solution passing through $u$. In particular, as long as no solution has been returned, the minimum value $f_{\min} = \min_{u \in OPEN} f(u)$ is a lower bound on $C^*$, hence $f_{\min} \leq C^*$.

PFS can return a solution only when it selects a goal state $n$. The selected state is either selected from FOCAL or selected as the best state in OPEN. If $n$ is selected from FOCAL, then by definition $f(n) \leq w f_{\min}$. If $n$ is selected as the best state in OPEN, then $f(n)=f_{\min} \leq w f_{\min}$ because $w \geq 1$. Therefore, in both cases,

$$
f(n) \leq w f_{\min} \leq w C^*.
$$

Since $n$ is a goal state and $h(n)=0$, we have $f(n)=g(n)$. Thus, the returned solution cost satisfies

$$
g(n) \leq w C^*.
$$

This proves the claim.

The next lemma clarifies a basic property of bounded-suboptimal focal search. It replaces the overly strong statement that all states with $f(n) \leq C^*/w$ must be expanded.

**Lemma 1.** Before PFS or classical FS can return a goal state with solution cost at least $C^*$, all states in OPEN with $f(n) < C^*/w$ must have ceased to be the minimum-$f$ frontier. In particular, the algorithm cannot return a goal from FOCAL while $f_{\min} < C^*/w$.

**Proof.** Suppose $f_{\min} < C^*/w$. Then every state $n$ in FOCAL satisfies

$$
f(n) \leq w f_{\min} < C^*.
$$

However, any goal state $g$ has $f(g)=g(g)$, which is at least $C^*$ by optimality of $C^*$. Therefore, no goal state can be contained in FOCAL while $f_{\min} < C^*/w$. Hence, the search frontier must advance until $f_{\min} \geq C^*/w$ before a goal state can be returned from FOCAL. The case $f_{\min}=C^*/w$ depends on tie-breaking and is therefore not stated as a strict expansion requirement.

We next discuss the effect of the probability parameter. This result is intended as an explanatory analysis rather than a domain-independent performance guarantee.

**Lemma 2.** Assume that, during a phase of the search, classical FS selects the minimum-$f$ state from FOCAL with probability at most $1/(\alpha k)$ at iteration $k$, where $\alpha>0$, while PFS selects the best state in OPEN with probability $1-p>0$. Then the expected number of OPEN-head expansions after $n$ iterations is $O(\log n)$ for classical FS under this model, but $\Theta(n(1-p))$ for PFS.

**Proof.** Under the stated model, the expected number of times classical FS selects the minimum-$f$ state from FOCAL after $n$ iterations is bounded by

$$
\sum_{k=1}^{n} \frac{1}{\alpha k}
= \frac{1}{\alpha} H_n
= O(\log n),
$$

where $H_n$ is the $n$-th harmonic number. In contrast, PFS explicitly selects the best state in OPEN with probability $1-p$ at each iteration. Therefore, its expected number of OPEN-head expansions after $n$ iterations is

$$
n(1-p) = \Theta(n(1-p)).
$$

For any fixed $p<1$, this quantity grows linearly in $n$, whereas the corresponding quantity for classical FS grows logarithmically under the simplified model. This explains why PFS may increase $f_{\min}$, and thus enlarge FOCAL, more aggressively than classical FS.

The assumptions in the preceding lemma are not meant to describe every search domain. Many practical domains have plateaus, duplicated $f$ values, and highly nonuniform heuristic distributions. The lemma should therefore be interpreted as a motivation for PFS rather than as a universal dominance result.

## Experimental Design

We evaluate PFS on several standard search domains:

1. **Sliding-tile puzzles:** 4-by-4 and 5-by-5 puzzle instances generated by random walks from the goal state. The Manhattan distance heuristic is used.
2. **Pancake problem:** random pancake permutations are solved using a landmark-based or gap-based admissible heuristic.
3. **Traveling salesman problem:** instances are solved in a shortest-path search formulation using a minimum spanning tree lower bound.
4. **Generalized covering traveling salesman problem:** instances are solved using an MST-based lower-bound heuristic adapted to the covering structure.

For each domain, we compare the following algorithms:

1. A*, as an optimal baseline when computationally feasible.
2. Weighted A*, as a standard bounded-suboptimal baseline.
3. Classical Focal Search, corresponding to PFS with $p=1$.
4. PFS with several values of $p$.

The following performance metrics are reported:

1. Solution cost and relative optimality gap.
2. Wall-clock runtime.
3. Number of generated and expanded states.
4. Success rate under a fixed time or memory limit.
5. Anytime behavior, measured by the cost of the best solution found over time.

To analyze the sensitivity of PFS, we vary the suboptimality factor $w$ and the focal probability $p$. In particular, we test

$$
p \in \{0, 0.25, 0.5, 0.75, 1.0\},
$$

where $p=1$ corresponds to classical FS and $p=0$ corresponds to always expanding the best state in OPEN. This design allows us to quantify whether intermediate values of $p$ provide a useful balance between FOCAL exploitation and OPEN-frontier advancement.

## Discussion

PFS is motivated by the observation that the size of the focal list is controlled by the threshold $w f_{\min}$. Classical FS may delay the growth of this threshold because it repeatedly selects states according to the secondary priority function. PFS addresses this issue by deliberately selecting the best state in OPEN with probability $1-p$. This simple modification can accelerate the increase of $f_{\min}$ while still preserving the bounded-suboptimality guarantee.

The value of $p$ determines the search behavior. A large $p$ emphasizes the secondary priority function and behaves similarly to classical FS. A small $p$ emphasizes the primary $f$ ordering and behaves more like A*. Intermediate values may be useful when the secondary priority is informative but the focal list grows too slowly under classical FS.

## Conclusion

This paper introduced Probabilistic Focal Search, a simple probabilistic variant of Focal Search. PFS alternates between expanding the best state in FOCAL and the best state in OPEN. The method preserves the standard $w$-suboptimality guarantee under an admissible heuristic and provides a tunable mechanism for balancing secondary-priority guidance against lower-bound progression. Future work includes evaluating adaptive strategies for updating $p$ during the search, studying the behavior of PFS in anytime settings, and testing the method on additional domains with large plateaus or weak heuristics.


## Appendix A: Heuristics for Classical and Inverse $n$-Puzzle

This appendix summarizes lightweight admissible heuristics for n-puzzle puzzles. These heuristics are suitable for A*, Weighted A*, Focal Search, PFS, DPS, and PDPS. The focus is on Manhattan distance and linear conflict, because they are easy to implement and have low computational overhead.

Consider an $m \times m$ puzzle board with

$$
N = m^2 - 1
$$

numbered tiles and one blank tile. A state is denoted by $s$. For each tile $i \in \{1,\ldots,N\}$, let

$$
\operatorname{pos}_s(i) = (r_s(i), c_s(i))
$$

be the current position of tile $i$, and let

$$
\operatorname{goal}(i) = (r^*(i), c^*(i))
$$

be its goal position. The Manhattan distance of tile $i$ is

$$
MD_i(s) = |r_s(i)-r^*(i)| + |c_s(i)-c^*(i)|.
$$

The total Manhattan distance is

$$
MD(s) = \sum_{i=1}^{N} MD_i(s).
$$

### A.1 Classical $n$-Puzzle

In the classical $n$-puzzle, every move has unit cost:

$$
c_i = 1, \qquad \forall i=1,\ldots,N.
$$

Therefore, the solution cost is exactly the number of moves.

#### A.1.1 Manhattan Distance

The standard admissible heuristic is

$$
h_{\mathrm{MD}}(s) = \sum_{i=1}^{N} MD_i(s).
$$

This heuristic is admissible because one move can change the Manhattan distance of only one tile by at most one. Hence, tile $i$ must be moved at least $MD_i(s)$ times before reaching its goal position.

#### A.1.2 Linear Conflict

Two tiles $i$ and $j$ are in **linear conflict** if they satisfy one of the following two conditions:

1. They are in the same row, both have their goal positions in that row, but their goal-column order is reversed.
2. They are in the same column, both have their goal positions in that column, but their goal-row order is reversed.

A linear conflict implies that at least one of the two tiles must leave the current row or column and later come back. Therefore, each tile removed to resolve such conflicts contributes at least two additional moves.

#### A.1.3 Computing Linear Conflict by LIS

A convenient way to compute linear conflict is to use the longest increasing subsequence (LIS).

For each row $r$, form the sequence

$$
A_r = (a_1,a_2,\ldots,a_k),
$$

where $a_t$ is the goal column of the $t$-th tile in row $r$, after removing:

1. the blank tile;
2. all tiles whose goal row is not $r$.

If $A_r$ is increasing, then the row has no row-based linear conflict. Otherwise, the minimum number of tiles that must leave the row is

$$
k - \operatorname{LIS}(A_r),
$$

where $\operatorname{LIS}(A_r)$ is the length of the longest increasing subsequence of $A_r$. Thus, the row contribution is

$$
LC_{\mathrm{row}}(r) = 2\left(k - \operatorname{LIS}(A_r)\right).
$$

Similarly, for each column $c$, form the sequence

$$
B_c = (b_1,b_2,\ldots,b_\ell),
$$

where $b_t$ is the goal row of the $t$-th tile in column $c$, after removing:

1. the blank tile;
2. all tiles whose goal column is not $c$.

The column contribution is

$$
LC_{\mathrm{col}}(c) = 2\left(\ell - \operatorname{LIS}(B_c)\right).
$$

The total linear-conflict term is

$$
LC(s) = \sum_{r=1}^{m} LC_{\mathrm{row}}(r) + \sum_{c=1}^{m} LC_{\mathrm{col}}(c).
$$

The Manhattan-plus-linear-conflict heuristic is therefore

$$
\boxed{
h_{\mathrm{LC}}(s)
=
\sum_{i=1}^{N} MD_i(s)
+
2\sum_{r=1}^{m}\left(k_r - \operatorname{LIS}(A_r)\right)
+
2\sum_{c=1}^{m}\left(\ell_c - \operatorname{LIS}(B_c)\right)
}.
$$

Here,

$$
k_r = |A_r|, \qquad \ell_c = |B_c|.
$$

This heuristic dominates Manhattan distance:

$$
h_{\mathrm{LC}}(s) \geq h_{\mathrm{MD}}(s),
$$

and remains admissible.

#### A.1.4 Implementation Guide for Linear Conflict

A simple implementation consists of the following steps.

**Step 1: Precompute goal positions.**  
Create two arrays:

$$
goalRow[i], \qquad goalCol[i].
$$

They store the goal row and goal column of each tile $i$.

**Step 2: Compute Manhattan distance.**  
For each tile $i \neq 0$ currently at $(r,c)$, add

$$
|r-goalRow[i]| + |c-goalCol[i]|.
$$

**Step 3: Compute row conflicts.**  
For each row $r$, scan columns from left to right. If a tile $i \neq 0$ satisfies

$$
goalRow[i] = r,
$$

append $goalCol[i]$ to $A_r$. Then add

$$
2\left(|A_r| - \operatorname{LIS}(A_r)\right)
$$

to the heuristic.

**Step 4: Compute column conflicts.**  
For each column $c$, scan rows from top to bottom. If a tile $i \neq 0$ satisfies

$$
goalCol[i] = c,
$$

append $goalRow[i]$ to $B_c$. Then add

$$
2\left(|B_c| - \operatorname{LIS}(B_c)\right)
$$

to the heuristic.

**Step 5: Return the final value.**

$$
h_{\mathrm{LC}}(s) = h_{\mathrm{MD}}(s) + LC(s).
$$

#### A.1.5 Complexity

For an $m \times m$ board, each row or column contains at most $m$ tiles. If LIS is computed by a simple dynamic programming algorithm in $O(m^2)$ time, the total complexity is

$$
O(m^3).
$$

If LIS is computed in $O(m \log m)$ time, the total complexity is

$$
O(m^2 \log m).
$$

For the 15-puzzle and 24-puzzle, $m$ is small, so the simple $O(m^2)$ LIS implementation per row or column is usually sufficient.

### A.2 Inverse $n$-Puzzle

In the inverse $n$-puzzle, the cost of moving tile $i$ is the inverse of its face value:

$$
c_i = \frac{1}{i}.
$$

Thus, moving small-numbered tiles is more expensive, while moving large-numbered tiles is cheaper. Unlike the classical unit-cost case, solution cost and solution length are no longer identical.

#### A.2.1 Weighted Manhattan Distance

The natural admissible cost heuristic is weighted Manhattan distance:

$$
h_{\mathrm{WMD}}(s)
=
\sum_{i=1}^{N} c_i MD_i(s)
=
\sum_{i=1}^{N} \frac{MD_i(s)}{i}.
$$

Equivalently,

$$
\boxed{
h_{\mathrm{WMD}}(s)
=
\sum_{i=1}^{N} \frac{MD_i(s)}{i}
}.
$$

This heuristic is admissible because tile $i$ must be moved at least $MD_i(s)$ times, and each move of tile $i$ costs $1/i$.

For algorithms such as EES, PFS, or PDPS that may also benefit from a distance-to-go estimate, one can use the unweighted Manhattan distance

$$
d_{\mathrm{MD}}(s) = \sum_{i=1}^{N} MD_i(s).
$$

Here, $h_{\mathrm{WMD}}(s)$ estimates remaining cost, whereas $d_{\mathrm{MD}}(s)$ estimates remaining solution length.

#### A.2.2 Weighted Linear Conflict

In the inverse $n$-puzzle, a linear conflict between tiles $i$ and $j$ still implies that at least one of them must leave the current row or column and later come back. If tile $i$ is selected to resolve such a conflict, the additional cost is at least

$$
2c_i = \frac{2}{i}.
$$

Therefore, each tile has a different removal weight:

$$
w_i = 2c_i = \frac{2}{i}.
$$

#### A.2.3 Computing Weighted Linear Conflict by Weighted LIS

For each row $r$, form the ordered tile sequence

$$
T_r = (i_1,i_2,\ldots,i_k),
$$

where each tile $i_t$ is currently in row $r$ and has goal row $r$. The associated key of tile $i_t$ is its goal column:

$$
a_t = goalCol[i_t].
$$

If we keep an increasing subsequence of these keys, the kept tiles do not conflict with each other. All other tiles must leave the row and come back. Since removing tile $i$ has cost $2/i$, the best admissible lower bound is obtained by keeping an increasing subsequence with maximum total weight.

Let

$$
\operatorname{WLIS}(T_r)
$$

be the maximum total weight of an increasing subsequence of $T_r$, where tile $i$ has weight

$$
w_i = \frac{2}{i}.
$$

The total weight of all row-eligible tiles is

$$
W(T_r) = \sum_{i\in T_r}\frac{2}{i}.
$$

The weighted row-conflict contribution is then

$$
WLC_{\mathrm{row}}(r) = W(T_r) - \operatorname{WLIS}(T_r).
$$

Similarly, for each column $c$, form the ordered tile sequence $Q_c$ consisting of tiles currently in column $c$ whose goal column is also $c$. The key is now the goal row. The weighted column-conflict contribution is

$$
WLC_{\mathrm{col}}(c) = W(Q_c) - \operatorname{WLIS}(Q_c).
$$

The total weighted linear-conflict term is

$$
WLC(s)
=
\sum_{r=1}^{m} WLC_{\mathrm{row}}(r)
+
\sum_{c=1}^{m} WLC_{\mathrm{col}}(c).
$$

The weighted linear-conflict heuristic is

$$
\boxed{
h_{\mathrm{WLC}}(s)
=
\sum_{i=1}^{N} \frac{MD_i(s)}{i}
+
\sum_{r=1}^{m}\left[W(T_r)-\operatorname{WLIS}(T_r)\right]
+
\sum_{c=1}^{m}\left[W(Q_c)-\operatorname{WLIS}(Q_c)\right]
}.
$$

This heuristic dominates weighted Manhattan distance:

$$
h_{\mathrm{WLC}}(s) \geq h_{\mathrm{WMD}}(s),
$$

and remains admissible.

#### A.2.4 Implementation Guide for Weighted Linear Conflict

A simple implementation consists of the following steps.

**Step 1: Compute weighted Manhattan distance.**  
For each tile $i \neq 0$ currently at $(r,c)$, add

$$
\frac{|r-goalRow[i]| + |c-goalCol[i]|}{i}.
$$

**Step 2: Compute weighted row conflicts.**  
For each row $r$, scan columns from left to right. If a tile $i \neq 0$ satisfies

$$
goalRow[i] = r,
$$

append tile $i$ to $T_r$, with key $goalCol[i]$ and weight

$$
w_i = \frac{2}{i}.
$$

Then add

$$
W(T_r) - \operatorname{WLIS}(T_r)
$$

to the heuristic.

**Step 3: Compute weighted column conflicts.**  
For each column $c$, scan rows from top to bottom. If a tile $i \neq 0$ satisfies

$$
goalCol[i] = c,
$$

append tile $i$ to $Q_c$, with key $goalRow[i]$ and weight

$$
w_i = \frac{2}{i}.
$$

Then add

$$
W(Q_c) - \operatorname{WLIS}(Q_c)
$$

to the heuristic.

**Step 4: Return the final value.**

$$
h_{\mathrm{WLC}}(s) = h_{\mathrm{WMD}}(s) + WLC(s).
$$

#### A.2.5 Computing Weighted LIS

For a sequence

$$
T = (i_1,i_2,\ldots,i_k),
$$

let each item $i_t$ have key $a_t$ and weight $w_{i_t}$. The weighted LIS value can be computed by dynamic programming:

$$
DP[t]
=
w_{i_t}
+
\max\{DP[q] : q<t,\ a_q<a_t\}.
$$

If there is no $q<t$ such that $a_q<a_t$, then

$$
DP[t]=w_{i_t}.
$$

Finally,

$$
\operatorname{WLIS}(T) = \max_{1\leq t\leq k} DP[t].
$$

Since each row or column has at most $m$ tiles, an $O(m^2)$ dynamic-programming implementation is typically fast enough for practical n-puzzle experiments.

### A.3 Recommended Heuristics

For the classical unit-cost $n$-puzzle, the recommended lightweight heuristic is

$$
\boxed{
h_{\mathrm{classic}}(s)
=
h_{\mathrm{LC}}(s)
=
\sum_{i=1}^{N} MD_i(s) + LC(s)
}.
$$

For the inverse $n$-puzzle, the recommended lightweight cost heuristic is

$$
\boxed{
h_{\mathrm{inverse}}(s)
=
h_{\mathrm{WLC}}(s)
=
\sum_{i=1}^{N}\frac{MD_i(s)}{i} + WLC(s)
}.
$$

When the search algorithm needs a separate distance estimate, use

$$
\boxed{
d(s) = \sum_{i=1}^{N} MD_i(s)
}.
$$
