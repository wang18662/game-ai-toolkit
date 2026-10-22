#include <gtest/gtest.h>

#include <functional>
#include <memory>

#include "gameai/core/behavior_tree.hpp"

using namespace gameai;

namespace {
// Minimal views — the BT nodes below only touch blackboard/flags.
AgentView make_agent() { return AgentView{}; }
WorldView make_world() { return WorldView{}; }
}  // namespace

TEST(BehaviorTree, sequence_fails_fast) {
    int calls = 0;
    auto fail = std::make_unique<Action>([&](const AgentView&, const WorldView&, Blackboard&) {
        calls++;
        return Status::Failure;
    });
    auto succ = std::make_unique<Action>([&](const AgentView&, const WorldView&, Blackboard&) {
        calls++;
        return Status::Success;
    });
    std::vector<std::unique_ptr<Node>> kids;
    kids.push_back(std::move(fail));
    kids.push_back(std::move(succ));
    Sequence seq(std::move(kids));

    Blackboard bb;
    EXPECT_EQ(seq.tick(make_agent(), make_world(), bb), Status::Failure);
    EXPECT_EQ(calls, 1);  // second child must NOT run after a failure
}

TEST(BehaviorTree, sequence_all_success) {
    int calls = 0;
    auto mk = [&](Status s) {
        return std::make_unique<Action>([&](const AgentView&, const WorldView&, Blackboard&) {
            calls++;
            return s;
        });
    };
    std::vector<std::unique_ptr<Node>> kids;
    kids.push_back(mk(Status::Success));
    kids.push_back(mk(Status::Success));
    Sequence seq(std::move(kids));

    Blackboard bb;
    EXPECT_EQ(seq.tick(make_agent(), make_world(), bb), Status::Success);
    EXPECT_EQ(calls, 2);
}

TEST(BehaviorTree, selector_succeeds_on_first_non_failure) {
    int calls = 0;
    auto fail = std::make_unique<Action>([&](const AgentView&, const WorldView&, Blackboard&) {
        calls++;
        return Status::Failure;
    });
    auto succ = std::make_unique<Action>([&](const AgentView&, const WorldView&, Blackboard&) {
        calls++;
        return Status::Success;
    });
    std::vector<std::unique_ptr<Node>> kids;
    kids.push_back(std::move(fail));
    kids.push_back(std::move(succ));
    Selector sel(std::move(kids));

    Blackboard bb;
    EXPECT_EQ(sel.tick(make_agent(), make_world(), bb), Status::Success);
    EXPECT_EQ(calls, 2);  // first failed, second ran and succeeded
}

TEST(BehaviorTree, selector_all_fail) {
    auto fail = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Failure; });
    auto fail2 = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Failure; });
    std::vector<std::unique_ptr<Node>> kids;
    kids.push_back(std::move(fail));
    kids.push_back(std::move(fail2));
    Selector sel(std::move(kids));

    Blackboard bb;
    EXPECT_EQ(sel.tick(make_agent(), make_world(), bb), Status::Failure);
}

TEST(BehaviorTree, inverter_flips_success_failure) {
    auto s = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Success; });
    auto f = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Failure; });
    auto r = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Running; });

    Blackboard bb;
    EXPECT_EQ(Inverter(std::move(s)).tick(make_agent(), make_world(), bb), Status::Failure);
    EXPECT_EQ(Inverter(std::move(f)).tick(make_agent(), make_world(), bb), Status::Success);
    EXPECT_EQ(Inverter(std::move(r)).tick(make_agent(), make_world(), bb), Status::Running);
}

TEST(BehaviorTree, condition_converts_bool) {
    auto yes = std::make_unique<Condition>(
        [](const AgentView&, const WorldView&, Blackboard&) { return true; });
    auto no = std::make_unique<Condition>(
        [](const AgentView&, const WorldView&, Blackboard&) { return false; });

    Blackboard bb;
    EXPECT_EQ(yes->tick(make_agent(), make_world(), bb), Status::Success);
    EXPECT_EQ(no->tick(make_agent(), make_world(), bb), Status::Failure);
}

TEST(BehaviorTree, composite_nesting) {
    // Selector[ Sequence[ fail, success ], success ]  -> second child of selector wins
    auto fail = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Failure; });
    auto succ = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Success; });
    std::vector<std::unique_ptr<Node>> seq_kids;
    seq_kids.push_back(std::move(fail));
    seq_kids.push_back(std::move(succ));
    auto seq = std::make_unique<Sequence>(std::move(seq_kids));

    auto win = std::make_unique<Action>(
        [](const AgentView&, const WorldView&, Blackboard&) { return Status::Success; });
    std::vector<std::unique_ptr<Node>> sel_kids;
    sel_kids.push_back(std::move(seq));     // Sequence fails fast (first child fails)
    sel_kids.push_back(std::move(win));     // Selector then tries this and succeeds
    Selector sel(std::move(sel_kids));

    Blackboard bb;
    EXPECT_EQ(sel.tick(make_agent(), make_world(), bb), Status::Success);
}
