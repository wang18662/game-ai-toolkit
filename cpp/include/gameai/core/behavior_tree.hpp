#pragma once

#include <functional>
#include <map>
#include <memory>
#include <vector>

#include "utility.hpp"  // AgentView, WorldView

namespace gameai {

enum class Status { Success = 1, Failure = 2, Running = 3 };

// Shared scratch memory for the tree (mirrors Python blackboard usage in BT).
using Blackboard = std::map<std::string, double>;

// GoF Composite: a node ticked with (agent, world, blackboard).
struct Node {
    virtual ~Node() = default;
    virtual Status tick(const AgentView& agent, const WorldView& world, Blackboard& bb) = 0;
};

using ActionFn = std::function<Status(const AgentView&, const WorldView&, Blackboard&)>;
using ConditionFn = std::function<bool(const AgentView&, const WorldView&, Blackboard&)>;

class Action : public Node {
public:
    explicit Action(ActionFn fn) : fn_(std::move(fn)) {}
    Status tick(const AgentView& a, const WorldView& w, Blackboard& bb) override { return fn_(a, w, bb); }

private:
    ActionFn fn_;
};

class Condition : public Node {
public:
    explicit Condition(ConditionFn fn) : fn_(std::move(fn)) {}
    Status tick(const AgentView& a, const WorldView& w, Blackboard& bb) override {
        return fn_(a, w, bb) ? Status::Success : Status::Failure;
    }

private:
    ConditionFn fn_;
};

class Composite : public Node {
public:
    explicit Composite(std::vector<std::unique_ptr<Node>> children)
        : children_(std::move(children)) {}

protected:
    std::vector<std::unique_ptr<Node>> children_;
};

// Run children in order; fail fast on first non-success.
class Sequence : public Composite {
public:
    using Composite::Composite;
    Status tick(const AgentView& a, const WorldView& w, Blackboard& bb) override {
        for (auto& c : children_) {
            Status s = c->tick(a, w, bb);
            if (s != Status::Success) return s;
        }
        return Status::Success;
    }
};

// Try children in order; succeed on first non-failure.
class Selector : public Composite {
public:
    using Composite::Composite;
    Status tick(const AgentView& a, const WorldView& w, Blackboard& bb) override {
        for (auto& c : children_) {
            Status s = c->tick(a, w, bb);
            if (s != Status::Failure) return s;
        }
        return Status::Failure;
    }
};

class Inverter : public Node {
public:
    explicit Inverter(std::unique_ptr<Node> child) : child_(std::move(child)) {}
    Status tick(const AgentView& a, const WorldView& w, Blackboard& bb) override {
        Status s = child_->tick(a, w, bb);
        if (s == Status::Success) return Status::Failure;
        if (s == Status::Failure) return Status::Success;
        return s;
    }

private:
    std::unique_ptr<Node> child_;
};

}  // namespace gameai
