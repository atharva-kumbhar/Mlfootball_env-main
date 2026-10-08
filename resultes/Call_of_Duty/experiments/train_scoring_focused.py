from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from organizer_rl_bot.policy import OrganizerRLOpponent
from reference_bot.policy import choose_action as reference_action
from soccer_env import GameConfig, SoccerEnv
from soccer_env.bots import aggressive_action, counter_action
from soccer_env.reinforcement import ReinforcementPolicy, reinforcement_reward


BASE_DIRECTORY = Path(__file__).resolve().parents[3] / "Mlfootball_env-main" / "participants"
EXPERIMENT_DIRECTORY = Path(__file__).resolve().parent


def scoring_reward(
    player_id: str,
    before: dict,
    after: dict,
    events: list[dict],
    action: dict,
) -> float:
    reward = reinforcement_reward(player_id, before, after, events, action)
    for event in events:
        if event.get("type") == "goal":
            reward += 75.0 if event.get("scorer") == player_id else -75.0

    sign = 1.0 if player_id == "player_1" else -1.0
    ball_progress = sign * (after["ball"]["y"] - before["ball"]["y"])
    reward += 0.02 * max(-8.0, min(8.0, ball_progress))
    return reward


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train an isolated Q-table with a stronger goal and attacking-progress objective."
    )
    parser.add_argument("--episodes", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=12409)
    parser.add_argument("--resume", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=EXPERIMENT_DIRECTORY / "scoring_focused_candidate.json",
    )
    parser.add_argument("--self-play-ratio", type=float, default=0.25)
    args = parser.parse_args()
    if args.episodes <= 0:
        parser.error("--episodes must be positive")
    if not 0 <= args.self_play_ratio <= 1:
        parser.error("--self-play-ratio must be between 0 and 1")

    config = GameConfig.from_json(BASE_DIRECTORY / "config" / "game.json")
    values = config.to_dict()
    values["kick_distances"] = tuple(values["kick_distances"])
    values["maximum_iterations"] = min(240, config.maximum_iterations)
    values["maximum_goals"] = min(5, config.maximum_goals)
    config = GameConfig(**values)

    learner = (
        ReinforcementPolicy.load(args.resume)
        if args.resume
        else ReinforcementPolicy(seed=args.seed, evaluation_epsilon=0.05, safety_margin=0.6)
    )
    learner.model_seed = args.seed
    learner.evaluation_epsilon = 0.05
    learner.safety_margin = 0.6

    organizer = OrganizerRLOpponent()
    opponents = [
        organizer.choose_action,
        reference_action,
        aggressive_action,
        counter_action,
    ]
    rng = random.Random(args.seed)
    totals = {"wins": 0, "draws": 0, "losses": 0}

    for episode in range(args.episodes):
        env = SoccerEnv(config)
        observations = env.reset(seed=args.seed + episode * 17)
        player_id = "player_1" if episode % 2 == 0 else "player_2"
        opponent_id = "player_2" if player_id == "player_1" else "player_1"
        opponent_policy = opponents[(episode // 2) % len(opponents)]
        if getattr(opponent_policy, "__self__", None) is organizer:
            organizer.start_episode()

        epsilon = max(0.035, 0.72 * math.exp(-4.2 * episode / max(1, args.episodes)))
        self_play = rng.random() < args.self_play_ratio
        while not env.done:
            before = env.state()
            if self_play:
                current_1 = observations["player_1"]
                current_2 = observations["player_2"]
                index_1 = learner.choose_index(current_1, epsilon)
                index_2 = learner.choose_index(current_2, epsilon)
                action_1 = learner.action_from_index(current_1, index_1)
                action_2 = learner.action_from_index(current_2, index_2)
                observations, info = env.step(action_1, action_2)
                learner.update(
                    current_1,
                    index_1,
                    scoring_reward("player_1", before, env.state(), info["events"], action_1),
                    observations["player_1"],
                    env.done,
                )
                learner.update(
                    current_2,
                    index_2,
                    scoring_reward("player_2", before, env.state(), info["events"], action_2),
                    observations["player_2"],
                    env.done,
                )
            else:
                current = observations[player_id]
                index = learner.choose_index(current, epsilon)
                action = learner.action_from_index(current, index)
                opponent_action = opponent_policy(observations[opponent_id])
                if rng.random() < 0.025:
                    legal_moves = observations[opponent_id]["action_space"]["move"][1:]
                    opponent_action = {"move": rng.choice(legal_moves)}
                actions = (
                    (action, opponent_action)
                    if player_id == "player_1"
                    else (opponent_action, action)
                )
                observations, info = env.step(*actions)
                learner.update(
                    current,
                    index,
                    scoring_reward(player_id, before, env.state(), info["events"], action),
                    observations[player_id],
                    env.done,
                )

        winner = env.result()["winner"]
        totals["draws" if winner is None else "wins" if winner == player_id else "losses"] += 1
        interval = max(1, args.episodes // 12)
        if (episode + 1) % interval == 0:
            print(
                f"episode={episode + 1}/{args.episodes} states={len(learner.q_table)} "
                f"epsilon={epsilon:.3f} W/D/L={totals['wins']}/{totals['draws']}/{totals['losses']}",
                flush=True,
            )

    learner.save(args.output)
    print(f"Saved {len(learner.q_table)} states to {args.output.resolve()}", flush=True)
    print(f"Training results: {totals}", flush=True)


if __name__ == "__main__":
    main()
