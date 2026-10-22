// Reads a shared JSON map (same schema as the Python core) and emits
// normalized outputs so the Python side can verify byte-identical results.
// Subcommands:
//   astar <map.json> <sx> <sy> <gx> <gy> [diagonal]
//   utility <hp> <max_hp> <sight> <attack> <enemy_exists 0|1> <enemy_dist>
//   fsm    <hp> <max_hp> <sight> <attack> <enemy_exists 0|1> <enemy_dist>

#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "gameai/core/astar.hpp"
#include "gameai/core/behavior_tree.hpp"
#include "gameai/core/fsm.hpp"
#include "gameai/core/utility.hpp"

using json = nlohmann::json;

namespace {

struct MapData {
    int width = 0, height = 0;
    std::set<std::pair<int, int>> obstacles;
};

MapData load_map(const std::string& path) {
    std::ifstream f(path);
    json data = json::parse(f);
    MapData m;
    m.width = data["width"].get<int>();
    m.height = data["height"].get<int>();
    for (auto& c : data["obstacles"]) {
        m.obstacles.insert({c[0].get<int>(), c[1].get<int>()});
    }
    return m;
}

std::string path_to_string(const std::vector<gameai::Vector2>& path) {
    if (path.empty()) return "NONE";
    std::ostringstream os;
    for (size_t i = 0; i < path.size(); ++i) {
        if (i) os << ";";
        os << static_cast<int>(std::round(path[i].x)) << "," << static_cast<int>(std::round(path[i].y));
    }
    return os.str();
}

// ---- skirmish FSM states (mirror Python sim.behaviors) ----
struct PatrolState : gameai::State {
    std::optional<std::string> update(const gameai::AgentView& a, const gameai::WorldView& w) override {
        if (w.enemy_exists && w.enemy_distance <= a.sight_range) return "enemy_spotted";
        return std::nullopt;
    }
};
struct ChaseState : gameai::State {
    std::optional<std::string> update(const gameai::AgentView& a, const gameai::WorldView& w) override {
        if (!w.enemy_exists) return "enemy_lost";
        if (w.enemy_distance <= a.attack_range) return "in_range";
        return std::nullopt;
    }
};
struct AttackState : gameai::State {
    std::optional<std::string> update(const gameai::AgentView& a, const gameai::WorldView& w) override {
        if (!w.enemy_exists) return "enemy_lost";
        if (w.enemy_distance > a.attack_range) return "out_of_range";
        if (a.hp < 0.3 * a.max_hp) return "low_hp";
        return std::nullopt;
    }
};
struct FleeState : gameai::State {
    std::optional<std::string> update(const gameai::AgentView& a, const gameai::WorldView& w) override {
        if (!w.enemy_exists) return "safe";
        if (w.enemy_distance > a.sight_range) return "safe";
        return std::nullopt;
    }
};

gameai::AgentView make_agent(double hp, double max_hp, double sight, double attack) {
    gameai::AgentView a;
    a.hp = hp; a.max_hp = max_hp; a.sight_range = sight; a.attack_range = attack;
    return a;
}
gameai::WorldView make_world(bool exists, double dist) {
    gameai::WorldView w;
    w.enemy_exists = exists; w.enemy_distance = dist;
    return w;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: parity_runner <astar|utility|fsm> ...\n";
        return 1;
    }
    std::string mode = argv[1];

    if (mode == "astar") {
        if (argc < 8) { std::cerr << "astar needs map sx sy gx gy [diag]\n"; return 1; }
        MapData m = load_map(argv[2]);
        int sx = std::stoi(argv[3]), sy = std::stoi(argv[4]);
        int gx = std::stoi(argv[5]), gy = std::stoi(argv[6]);
        bool diag = argc > 7 ? std::string(argv[7]) != "0" : true;
        auto walkable = [&](int x, int y) {
            if (x < 0 || y < 0 || x >= m.width || y >= m.height) return false;
            return m.obstacles.find({x, y}) == m.obstacles.end();
        };
        auto path = gameai::find_path({sx, sy}, {gx, gy}, walkable, gameai::Octile{}, gameai::UniformCost{}, diag);
        std::cout << path_to_string(path) << "\n";
        return 0;
    }

    if (mode == "utility" || mode == "fsm") {
        if (argc < 8) { std::cerr << mode << " needs hp max_hp sight attack exists dist\n"; return 1; }
        double hp = std::stod(argv[2]), max_hp = std::stod(argv[3]);
        double sight = std::stod(argv[4]), attack = std::stod(argv[5]);
        bool exists = std::string(argv[6]) == "1";
        double dist = std::stod(argv[7]);
        auto agent = make_agent(hp, max_hp, sight, attack);
        auto world = make_world(exists, dist);

        if (mode == "utility") {
            using namespace gameai;
            std::vector<Option> opts = {
                {"Advance", {{input_enemy_closeness, CurveType::Linear, 0.0, 8.0, 1.0}}},
                {"Attack",  {{input_in_attack_range, CurveType::Linear, 0.0, 1.0, 1.5}}},
                {"Retreat", {{input_retreat_score,    CurveType::Linear, 0.0, 1.0, 1.2}}},
            };
            auto [chosen, score] = decide(opts, agent, world);
            std::cout << chosen.name << "\n";
            return 0;
        }

        // fsm: build the 4 skirmish states, start in patrol, run one update
        std::map<std::string, std::unique_ptr<gameai::State>> states;
        states["patrol"] = std::make_unique<PatrolState>();
        states["chase"] = std::make_unique<ChaseState>();
        states["attack"] = std::make_unique<AttackState>();
        states["flee"] = std::make_unique<FleeState>();
        std::map<std::string, std::map<std::string, std::string>> tr = {
            {"patrol", {{"enemy_spotted", "chase"}}},
            {"chase", {{"in_range", "attack"}, {"enemy_lost", "patrol"}}},
            {"attack", {{"out_of_range", "chase"}, {"low_hp", "flee"}, {"enemy_lost", "patrol"}}},
            {"flee", {{"safe", "patrol"}}},
        };
        gameai::FSM fsm(std::move(states), tr, "patrol");
        fsm.update(agent, world);
        std::cout << fsm.current() << "\n";
        return 0;
    }

    std::cerr << "unknown mode: " << mode << "\n";
    return 1;
}
