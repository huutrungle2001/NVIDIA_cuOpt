#pragma once
#include "solver/problem.hpp"
#include <vector>
#include <string>
#include <tuple>
#include <set>

// Standalone GCTSP Heuristic classes
class GCTSPHeuristic : public Heuristic {
protected:
    int num_nodes;
    int depot;
    const std::vector<std::vector<double>>& dist_matrix;
    int num_customers;
    const std::vector<std::set<int>>& covering_sets;
    const std::vector<std::set<int>>& covering_sets_list;
    int quota;
public:
    GCTSPHeuristic(int nodes, int dep, const std::vector<std::vector<double>>& dist,
                   int customers, const std::vector<std::set<int>>& cov_sets,
                   const std::vector<std::set<int>>& cov_list,
                   int quota)
        : num_nodes(nodes), depot(dep), dist_matrix(dist),
          num_customers(customers), covering_sets(cov_sets),
          covering_sets_list(cov_list), quota(quota) {}
};

class GCTSPContractedMSTHeuristic : public GCTSPHeuristic {
public:
    using GCTSPHeuristic::GCTSPHeuristic;
    double evaluate(const State& state) override;
    std::string get_name() const override { return "contracted_mst"; }
};

class GCTSPGreedySetCoverHeuristic : public GCTSPHeuristic {
public:
    using GCTSPHeuristic::GCTSPHeuristic;
    double evaluate(const State& state) override;
    std::string get_name() const override { return "greedy_setcover"; }
};

class GCTSPZeroHeuristic : public GCTSPHeuristic {
public:
    using GCTSPHeuristic::GCTSPHeuristic;
    double evaluate(const State& state) override;
    std::string get_name() const override { return "zero"; }
};

class GCTSPDijkstraHeuristic : public GCTSPHeuristic {
private:
    std::vector<double> H;
    void precompute();
public:
    GCTSPDijkstraHeuristic(int nodes, int dep, const std::vector<std::vector<double>>& dist,
                           int customers, const std::vector<std::set<int>>& cov_sets,
                           const std::vector<std::set<int>>& cov_list,
                           int quota);
    double evaluate(const State& state) override;
    std::string get_name() const override { return "dijkstra"; }
};

class GCTSPProblem : public SearchProblem {
public:
    GCTSPProblem(int num_nodes, int depot, const std::vector<std::vector<double>>& dist_matrix,
                 int num_customers, const std::vector<std::vector<int>>& covering_sets,
                 int quota,
                 std::string h1_type = "contracted_mst",
                 std::string h2_type = "greedy_setcover");

    static bool is_solvable(int num_nodes, int num_customers, const std::vector<std::vector<int>>& covering_sets, int quota);

    State get_initial_state() override;
    bool is_goal(const State& state) override;
    std::vector<std::tuple<State, Action, double>> get_successors(const State& state) override;
    Action get_action(const State& parent_state, const State& child_state) override;
    DomainType get_domain_type() const override { return DomainType::CONTINUOUS_GRAPH; }

private:
    int num_nodes;
    int depot;
    std::vector<std::vector<double>> dist_matrix;
    int num_customers;
    int quota;
    std::vector<std::set<int>> covering_sets;
    int all_covered_mask;
    std::vector<int> node_covered_masks;
    std::vector<std::set<int>> covering_sets_list;
    State initial_state;
    std::string h1_type;
    std::string h2_type;
};

