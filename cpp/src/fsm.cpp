#include "gameai/core/fsm.hpp"

#include <stdexcept>

namespace gameai {

FSM::FSM(std::map<std::string, std::unique_ptr<State>> states,
         std::map<std::string, std::map<std::string, std::string>> transitions,
         std::string initial)
    : states_(std::move(states)), transitions_(std::move(transitions)), current_name_(std::move(initial)) {
    auto it = states_.find(current_name_);
    if (it == states_.end()) throw std::invalid_argument("initial state not in states");
    current_ = it->second.get();
}

void FSM::update(const AgentView& agent, const WorldView& world) {
    auto event = current_->update(agent, world);
    if (!event.has_value()) return;
    auto tr_it = transitions_.find(current_name_);
    if (tr_it == transitions_.end()) return;
    auto next_it = tr_it->second.find(*event);
    if (next_it == tr_it->second.end()) return;
    current_->onExit(agent, world);
    current_name_ = next_it->second;
    current_ = states_.at(current_name_).get();
    current_->onEnter(agent, world);
}

}  // namespace gameai
