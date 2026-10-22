#include <gtest/gtest.h>

#include "gameai/core/utility.hpp"

using namespace gameai;

TEST(Utility, highest_score_wins) {
    AgentView a; a.hp = 100; a.max_hp = 100; a.sight_range = 6; a.attack_range = 1.6;
    WorldView w; w.enemy_exists = true; w.enemy_distance = 1.0;  // in range, close

    std::vector<Option> opts = {
        {"Advance", {{input_enemy_closeness, CurveType::Linear, 0.0, 8.0, 1.0}}},
        {"Attack",  {{input_in_attack_range, CurveType::Linear, 0.0, 1.0, 1.5}}},
        {"Retreat", {{input_retreat_score,    CurveType::Linear, 0.0, 1.0, 1.2}}},
    };
    auto [chosen, score] = decide(opts, a, w);
    EXPECT_EQ(chosen.name, "Attack");
}

TEST(Utility, low_hp_picks_retreat) {
    AgentView a; a.hp = 10; a.max_hp = 100; a.sight_range = 6; a.attack_range = 1.6;
    WorldView w; w.enemy_exists = true; w.enemy_distance = 5.0;  // far, low hp

    std::vector<Option> opts = {
        {"Advance", {{input_enemy_closeness, CurveType::Linear, 0.0, 8.0, 1.0}}},
        {"Attack",  {{input_in_attack_range, CurveType::Linear, 0.0, 1.0, 1.5}}},
        {"Retreat", {{input_retreat_score,    CurveType::Linear, 0.0, 1.0, 1.2}}},
    };
    auto [chosen, score] = decide(opts, a, w);
    EXPECT_EQ(chosen.name, "Retreat");
}

TEST(Utility, sigmoid_within_unit) {
    double v = response_curve(CurveType::Sigmoid, 0.0);
    EXPECT_GE(v, 0.0);
    EXPECT_LE(v, 1.0);
}
