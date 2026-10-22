#pragma once

#include <map>
#include <memory>
#include <optional>
#include <string>

#include "utility.hpp"  // AgentView, WorldView

namespace gameai {

// GoF State: a single FSM state. update() returns a transition event name,
// or nullopt to stay in the current state.
struct State {
    virtual ~State() = default;
    virtual void onEnter(const AgentView& agent, const WorldView& world) {}
    virtual void onExit(const AgentView& agent, const WorldView& world) {}
    virtual std::optional<std::string> update(const AgentView& agent, const WorldView& world) = 0;
};

// Finite state machine driving an agent through States via events.
class FSM {
public:
    FSM(std::map<std::string, std::unique_ptr<State>> states,
        std::map<std::string, std::map<std::string, std::string>> transitions,
        std::string initial);

    const std::string& current() const { return current_name_; }
    void update(const AgentView& agent, const WorldView& world);

private:
    std::map<std::string, std::unique_ptr<State>> states_;
    std::map<std::string, std::map<std::string, std::string>> transitions_;
    std::string current_name_;
    State* current_;
};

}  // namespace gameai
