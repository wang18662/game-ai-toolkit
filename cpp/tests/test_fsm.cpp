#include <gtest/gtest.h>

#include <map>
#include <memory>
#include <optional>
#include <string>

#include "gameai/core/fsm.hpp"

using namespace gameai;

namespace {
// Skirmish FSM states — identical condition logic to the Python sim.behaviors
// and to parity_runner.cpp, so this unit test also guards cross-language parity.
struct PatrolState : State {
    std::optional<std::string> update(const AgentView& a, const WorldView& w) override {
        if (w.enemy_exists && w.enemy_distance <= a.sight_range) return "enemy_spotted";
        return std::nullopt;
    }
};
struct ChaseState : State {
    std::optional<std::string> update(const AgentView& a, const WorldView& w) override {
        if (!w.enemy_exists) return "enemy_lost";
        if (w.enemy_distance <= a.attack_range) return "in_range";
        return std::nullopt;
    }
};
struct AttackState : State {
    std::optional<std::string> update(const AgentView& a, const WorldView& w) override {
        if (!w.enemy_exists) return "enemy_lost";
        if (w.enemy_distance > a.attack_range) return "out_of_range";
        if (a.hp < 0.3 * a.max_hp) return "low_hp";
        return std::nullopt;
    }
};
struct FleeState : State {
    std::optional<std::string> update(const AgentView& a, const WorldView& w) override {
        if (!w.enemy_exists) return "safe";
        if (w.enemy_distance > a.sight_range) return "safe";
        return std::nullopt;
    }
};

FSM make_skirmish_fsm() {
    std::map<std::string, std::unique_ptr<State>> states;
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
    return FSM(std::move(states), tr, "patrol");
}

AgentView agent(double hp, double max_hp, double sight, double attack) {
    AgentView a;
    a.hp = hp; a.max_hp = max_hp; a.sight_range = sight; a.attack_range = attack;
    return a;
}
WorldView world(bool exists, double dist) {
    WorldView w;
    w.enemy_exists = exists; w.enemy_distance = dist;
    return w;
}
}  // namespace

TEST(FSM, patrol_sees_enemy_transitions_to_chase) {
    FSM fsm = make_skirmish_fsm();
    fsm.update(agent(100, 100, 6, 1.6), world(true, 2.0));  // in sight
    EXPECT_EQ(fsm.current(), "chase");
}

TEST(FSM, patrol_no_enemy_stays) {
    FSM fsm = make_skirmish_fsm();
    fsm.update(agent(100, 100, 6, 1.6), world(false, 0.0));
    EXPECT_EQ(fsm.current(), "patrol");
}

TEST(FSM, patrol_enemy_far_beyond_sight_stays) {
    FSM fsm = make_skirmish_fsm();
    fsm.update(agent(100, 100, 6, 1.6), world(true, 20.0));
    EXPECT_EQ(fsm.current(), "patrol");
}

TEST(FSM, patrol_to_attack_in_one_range_step) {
    FSM fsm = make_skirmish_fsm();
    auto a = agent(100, 100, 6, 1.6);
    auto w = world(true, 1.0);  // in attack range -> chase then attack
    fsm.update(a, w);           // patrol -> chase
    fsm.update(a, w);           // chase -> attack
    EXPECT_EQ(fsm.current(), "attack");
}

TEST(FSM, low_hp_flees_from_attack) {
    FSM fsm = make_skirmish_fsm();
    auto a = agent(10, 100, 6, 1.6);  // 10% hp
    auto w = world(true, 1.0);        // in attack range
    fsm.update(a, w);  // patrol -> chase
    fsm.update(a, w);  // chase -> attack
    fsm.update(a, w);  // attack -> flee (low_hp)
    EXPECT_EQ(fsm.current(), "flee");
}
