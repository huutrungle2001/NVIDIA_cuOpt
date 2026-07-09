#include "solver/problems/gctsp.hpp"
#include "utils/graph.hpp"
#include <algorithm>
#include <limits>

GCTSPProblem::GCTSPProblem(int num_nodes, int depot, const std::vector<std::vector<double>>& dist_matrix,
                           int num_customers, const std::vector<std::vector<int>>& covering_sets_in,
                           int quota,
                           std::string h1_type,
                           std::string h2_type)
    : num_nodes(num_nodes), depot(depot), dist_matrix(dist_matrix), num_customers(num_customers),
      quota(quota), h1_type(h1_type), h2_type(h2_type) {
    
    covering_sets.resize(num_customers);
    for (int c = 0; c < num_customers; ++c) {
        covering_sets[c] = std::set<int>(covering_sets_in[c].begin(), covering_sets_in[c].end());
    }

    all_covered_mask = 0; // Unused, kept for header compatibility

    node_covered_masks.assign(num_nodes, 0); // Unused, kept for header compatibility
    covering_sets_list.assign(num_nodes, std::set<int>());
    for (int c = 0; c < num_customers; ++c) {
        for (int node : covering_sets[c]) {
            covering_sets_list[node].insert(c);
        }
    }

    // State: [curr_node, covered_0, covered_1, ..., covered_M-1]
    initial_state.resize(num_customers + 1, 0);
    initial_state[0] = depot;
    for (int c : covering_sets_list[depot]) {
        initial_state[c + 1] = 1;
    }

    // Instantiate primary heuristic
    if (h1_type == "none" || h1_type == "zero") {
        primary_heuristic = std::make_shared<GCTSPZeroHeuristic>(num_nodes, depot, this->dist_matrix, num_customers, this->covering_sets, this->covering_sets_list, this->quota);
    } else if (h1_type == "dijkstra") {
        primary_heuristic = std::make_shared<GCTSPDijkstraHeuristic>(num_nodes, depot, this->dist_matrix, num_customers, this->covering_sets, this->covering_sets_list, this->quota);
    } else {
        primary_heuristic = std::make_shared<GCTSPContractedMSTHeuristic>(num_nodes, depot, this->dist_matrix, num_customers, this->covering_sets, this->covering_sets_list, this->quota);
    }

    // Instantiate secondary heuristic
    if (h2_type == "none") {
        secondary_heuristic = primary_heuristic;
    } else if (h2_type == "contracted_mst") {
        secondary_heuristic = std::make_shared<GCTSPContractedMSTHeuristic>(num_nodes, depot, this->dist_matrix, num_customers, this->covering_sets, this->covering_sets_list, this->quota);
    } else if (h2_type == "dijkstra") {
        secondary_heuristic = std::make_shared<GCTSPDijkstraHeuristic>(num_nodes, depot, this->dist_matrix, num_customers, this->covering_sets, this->covering_sets_list, this->quota);
    } else {
        secondary_heuristic = std::make_shared<GCTSPGreedySetCoverHeuristic>(num_nodes, depot, this->dist_matrix, num_customers, this->covering_sets, this->covering_sets_list, this->quota);
    }
}

State GCTSPProblem::get_initial_state() {
    return initial_state;
}

bool GCTSPProblem::is_goal(const State& state) {
    int curr_node = state[0];
    if (curr_node != depot) return false;
    
    int num_covered = 0;
    for (int c = 0; c < num_customers; ++c) {
        if (state[c + 1] == 1) {
            num_covered++;
        }
    }
    return num_covered >= quota;
}

std::vector<std::tuple<State, Action, double>> GCTSPProblem::get_successors(const State& state) {
    int curr_node = state[0];
    std::vector<std::tuple<State, Action, double>> successors;

    int num_covered = 0;
    for (int c = 0; c < num_customers; ++c) {
        if (state[c + 1] == 1) {
            num_covered++;
        }
    }

    if (num_covered >= quota) {
        if (curr_node != depot) {
            double cost = dist_matrix[curr_node][depot];
            State next_state = state;
            next_state[0] = depot;
            successors.emplace_back(next_state, "RETURN_TO_DEPOT", cost);
        }
    } else {
        for (int next_node = 0; next_node < num_nodes; ++next_node) {
            if (next_node != curr_node) {
                double cost = dist_matrix[curr_node][next_node];
                State next_state = state;
                next_state[0] = next_node;
                // Add new covered customers
                for (int c : covering_sets_list[next_node]) {
                    next_state[c + 1] = 1;
                }
                successors.emplace_back(next_state, "VISIT_" + std::to_string(next_node), cost);
            }
        }
    }
    return successors;
}

double GCTSPContractedMSTHeuristic::evaluate(const State& state) {
    int curr_node = state[0];

    int num_covered = 0;
    std::vector<int> uncovered;
    for (int c = 0; c < num_customers; ++c) {
        if (state[c + 1] == 1) {
            num_covered++;
        } else {
            if (!covering_sets[c].empty()) {
                uncovered.push_back(c);
            }
        }
    }

    int remaining_to_cover = quota - num_covered;
    if (remaining_to_cover <= 0) {
        if (curr_node != depot) {
            return dist_matrix[curr_node][depot];
        }
        return 0.0;
    }

    if (uncovered.size() < static_cast<size_t>(remaining_to_cover)) {
        return std::numeric_limits<double>::infinity();
    }

    std::vector<int> uncovered_sorted = uncovered;
    std::sort(uncovered_sorted.begin(), uncovered_sorted.end(), [this](int a, int b) {
        if (covering_sets[a].size() != covering_sets[b].size()) {
            return covering_sets[a].size() < covering_sets[b].size();
        }
        return a < b;
    });

    int C_max = 1;
    for (int w = 0; w < num_nodes; ++w) {
        int count = 0;
        for (int c : covering_sets_list[w]) {
            if (state[c + 1] == 0) {
                count++;
            }
        }
        if (count > C_max) {
            C_max = count;
        }
    }
    int K_req = (remaining_to_cover + C_max - 1) / C_max;

    std::vector<int> independent_customers;
    std::set<int> blocked_nodes;
    for (int c : uncovered_sorted) {
        const auto& cov_nodes = covering_sets[c];
        if (cov_nodes.empty()) {
            return std::numeric_limits<double>::infinity();
        }

        bool intersects = false;
        for (int node : cov_nodes) {
            if (blocked_nodes.count(node)) {
                intersects = true;
                break;
            }
        }

        if (!intersects) {
            independent_customers.push_back(c);
            blocked_nodes.insert(cov_nodes.begin(), cov_nodes.end());
        }
    }

    int K = independent_customers.size();
    if (K > K_req) {
        K = K_req;
        independent_customers.resize(K);
    }
    int num_contracted_nodes = K + 2;

    auto get_contracted_dist = [this, curr_node, &independent_customers](int u, int v) -> double {
        if (u == v) return 0.0;

        if (u == 0) {
            if (v == 1) {
                return dist_matrix[curr_node][depot];
            } else {
                const auto& set_v = covering_sets[independent_customers[v - 2]];
                double min_d = std::numeric_limits<double>::infinity();
                for (int y : set_v) {
                    min_d = std::min(min_d, dist_matrix[curr_node][y]);
                }
                return min_d;
            }
        } else if (u == 1) {
            if (v == 0) {
                return dist_matrix[depot][curr_node];
            } else {
                const auto& set_v = covering_sets[independent_customers[v - 2]];
                double min_d = std::numeric_limits<double>::infinity();
                for (int y : set_v) {
                    min_d = std::min(min_d, dist_matrix[depot][y]);
                }
                return min_d;
            }
        } else {
            const auto& set_u = covering_sets[independent_customers[u - 2]];
            if (v == 0) {
                double min_d = std::numeric_limits<double>::infinity();
                for (int x : set_u) {
                    min_d = std::min(min_d, dist_matrix[x][curr_node]);
                }
                return min_d;
            } else if (v == 1) {
                double min_d = std::numeric_limits<double>::infinity();
                for (int x : set_u) {
                    min_d = std::min(min_d, dist_matrix[x][depot]);
                }
                return min_d;
            } else {
                const auto& set_v = covering_sets[independent_customers[v - 2]];
                double min_d = std::numeric_limits<double>::infinity();
                for (int x : set_u) {
                    for (int y : set_v) {
                        min_d = std::min(min_d, dist_matrix[x][y]);
                    }
                }
                return min_d;
            }
        }
    };

    return utils::prim_mst(num_contracted_nodes, get_contracted_dist);
}

double GCTSPGreedySetCoverHeuristic::evaluate(const State& state) {
    int curr_node = state[0];

    int num_covered = 0;
    std::vector<bool> uncovered(num_customers, false);
    int actual_uncovered_count = 0;
    for (int c = 0; c < num_customers; ++c) {
        if (state[c + 1] == 1) {
            num_covered++;
        } else {
            if (!covering_sets[c].empty()) {
                uncovered[c] = true;
                actual_uncovered_count++;
            }
        }
    }

    int remaining_to_cover = quota - num_covered;
    if (remaining_to_cover <= 0) {
        if (curr_node != depot) {
            return 1.0;
        }
        return 0.0;
    }

    if (actual_uncovered_count < remaining_to_cover) {
        return std::numeric_limits<double>::infinity();
    }

    int steps = 0;
    while (remaining_to_cover > 0) {
        int best_node = -1;
        int best_count = 0;
        for (int w = 0; w < num_nodes; ++w) {
            int count = 0;
            for (int c : covering_sets_list[w]) {
                if (uncovered[c]) {
                    count++;
                }
            }
            if (count > best_count) {
                best_count = count;
                best_node = w;
            }
        }

        if (best_node == -1 || best_count == 0) {
            return std::numeric_limits<double>::infinity();
        }

        for (int c : covering_sets_list[best_node]) {
            if (uncovered[c]) {
                uncovered[c] = false;
                remaining_to_cover--;
            }
        }
        steps++;
    }

    return static_cast<double>(steps + 1);
}

double GCTSPZeroHeuristic::evaluate(const State& state) {
    int curr_node = state[0];
    int num_covered = 0;
    for (int c = 0; c < num_customers; ++c) {
        if (state[c + 1] == 1) {
            num_covered++;
        }
    }
    if (num_covered >= quota && curr_node != depot) {
        return dist_matrix[curr_node][depot];
    }
    return 0.0;
}

Action GCTSPProblem::get_action(const State& parent_state, const State& child_state) {
    int num_covered = 0;
    for (int c = 0; c < num_customers; ++c) {
        if (parent_state[c + 1] == 1) {
            num_covered++;
        }
    }
    if (child_state[0] == depot && num_covered >= quota) {
        return "RETURN_TO_DEPOT";
    }
    return "VISIT_" + std::to_string(child_state[0]);
}

bool GCTSPProblem::is_solvable(int num_nodes, int num_customers, const std::vector<std::vector<int>>& covering_sets, int quota) {
    int coverable_count = 0;
    for (int c = 0; c < num_customers; ++c) {
        bool has_valid_node = false;
        for (int node : covering_sets[c]) {
            if (node >= 0 && node < num_nodes) {
                has_valid_node = true;
                break;
            }
        }
        if (has_valid_node) {
            coverable_count++;
        }
    }
    return coverable_count >= quota;
}

#include <queue>
#include <map>

GCTSPDijkstraHeuristic::GCTSPDijkstraHeuristic(int nodes, int dep, const std::vector<std::vector<double>>& dist,
                                               int customers, const std::vector<std::set<int>>& cov_sets,
                                               const std::vector<std::set<int>>& cov_list,
                                               int quota)
    : GCTSPHeuristic(nodes, dep, dist, customers, cov_sets, cov_list, quota) {
    precompute();
}

void GCTSPDijkstraHeuristic::precompute() {
    H.assign(quota + 1, std::numeric_limits<double>::infinity());
    H[0] = 0.0;

    // Dijkstra State: (distance, curr_node, covered_mask)
    using DState = std::pair<int, std::vector<char>>;
    
    struct Compare {
        bool operator()(const std::pair<double, DState>& a, const std::pair<double, DState>& b) const {
            return a.first > b.first;
        }
    };

    std::priority_queue<std::pair<double, DState>, std::vector<std::pair<double, DState>>, Compare> pq;
    std::map<DState, double> dists;

    // Initial state
    std::vector<char> initial_mask(num_customers, 0);
    for (int c : covering_sets_list[depot]) {
        if (c >= 0 && c < num_customers) {
            initial_mask[c] = 1;
        }
    }
    
    DState start_state = {depot, initial_mask};
    dists[start_state] = 0.0;
    pq.push({0.0, start_state});

    int unset_count = quota + 1;
    
    // Count initial covered
    int init_c = 0;
    for (char x : initial_mask) if (x) init_c++;
    for (int k = 0; k <= std::min(init_c, quota); ++k) {
        if (H[k] == std::numeric_limits<double>::infinity()) {
            H[k] = 0.0;
            unset_count--;
        }
    }

    int popped_states = 0;
    const int max_dijkstra_states = 50000; // safety limit to prevent OOM/timeouts on large datasets

    while (!pq.empty()) {
        if (unset_count <= 0) break;
        if (popped_states++ > max_dijkstra_states) {
            // Fill remaining unset H values using the last popped distance as a safe lower bound
            double fallback_d = pq.top().first;
            for (int k = 0; k <= quota; ++k) {
                if (H[k] == std::numeric_limits<double>::infinity()) {
                    H[k] = fallback_d;
                }
            }
            break;
        }

        auto [d, curr_s] = pq.top();
        pq.pop();

        if (d > dists[curr_s]) continue;

        int u = curr_s.first;
        const auto& mask = curr_s.second;

        // Expand to neighbors
        for (int v = 0; v < num_nodes; ++v) {
            if (v == u) continue;

            double cost = dist_matrix[u][v];
            double next_d = d + cost;

            std::vector<char> next_mask = mask;
            for (int c : covering_sets_list[v]) {
                if (c >= 0 && c < num_customers) {
                    next_mask[c] = 1;
                }
            }

            DState next_s = {v, next_mask};
            auto it = dists.find(next_s);
            if (it == dists.end() || next_d < it->second) {
                dists[next_s] = next_d;
                pq.push({next_d, next_s});

                // Update H values
                int c_count = 0;
                for (char x : next_mask) if (x) c_count++;
                for (int k = 0; k <= std::min(c_count, quota); ++k) {
                    if (H[k] == std::numeric_limits<double>::infinity()) {
                        H[k] = next_d;
                        unset_count--;
                    }
                }
            }
        }
    }
}

double GCTSPDijkstraHeuristic::evaluate(const State& state) {
    int curr_node = state[0];
    int num_covered = 0;
    for (int c = 0; c < num_customers; ++c) {
        if (state[c + 1] == 1) {
            num_covered++;
        }
    }
    int remaining = quota - num_covered;
    if (remaining <= 0) {
        if (curr_node != depot) {
            return dist_matrix[curr_node][depot];
        }
        return 0.0;
    }
    if (remaining > quota) remaining = quota;
    return H[remaining];
}
