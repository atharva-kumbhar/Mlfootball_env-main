from __future__ import annotations

import json
import heapq
import math
import random
from pathlib import Path
from typing import Any


DIRECTION_VECTORS = {
    "STAY": (0, 0),
    "UP": (0, 1),
    "UP_RIGHT": (1, 1),
    "RIGHT": (1, 0),
    "DOWN_RIGHT": (1, -1),
    "DOWN": (0, -1),
    "DOWN_LEFT": (-1, -1),
    "LEFT": (-1, 0),
    "UP_LEFT": (-1, 1),
}
MOVES = list(DIRECTION_VECTORS)
KICK_DIRECTIONS = [name for name in MOVES if name != "STAY"]
ACTION_COUNT = len(MOVES) + len(KICK_DIRECTIONS) * 3


def direction_toward(dx: float, dy: float, dead_zone: float = 1.0) -> str:
    horizontal = "" if abs(dx) <= dead_zone else ("RIGHT" if dx > 0 else "LEFT")
    vertical = "" if abs(dy) <= dead_zone else ("UP" if dy > 0 else "DOWN")
    return f"{vertical}_{horizontal}" if vertical and horizontal else vertical or horizontal or "STAY"


def _bucket(value: float, limits: tuple[float, ...]) -> int:
    return next((index for index, limit in enumerate(limits) if value < limit), len(limits))


def _sector(dx: float, dy: float) -> int:
    if abs(dx) + abs(dy) < 1e-9:
        return 8
    return int(round(math.atan2(dy, dx) / (math.pi / 4))) % 8


def _move_is_safe(observation: dict[str, Any], move: str) -> bool:
    if move == "STAY":
        return True
    state = observation["state"]
    me = state["players"][observation["player_id"]]
    field = state["field"]
    speed = float(field.get("player_speed", 4.0))
    radius = float(field.get("player_radius", 3.0))
    vx, vy = DIRECTION_VECTORS[move]
    length = math.hypot(vx, vy) or 1.0
    x = me["x"] + vx / length * speed
    y = me["y"] + vy / length * speed
    if x - radius < 0 or x + radius > field["width"] or y - radius < 0 or y + radius > field["height"]:
        return False
    for obstacle in state.get("obstacles", []):
        closest_x = min(max(x, obstacle["x"]), obstacle["x"] + obstacle["width"])
        closest_y = min(max(y, obstacle["y"]), obstacle["y"] + obstacle["height"])
        if math.hypot(x - closest_x, y - closest_y) < radius + 0.25:
            return False
    return True


def _safe_move(observation: dict[str, Any], preferred: str) -> str:
    preferred_vector = DIRECTION_VECTORS[preferred]
    choices = [move for move in MOVES if move != "STAY" and _move_is_safe(observation, move)]
    if not choices:
        return "STAY"

    state = observation["state"]
    me = state["players"][observation["player_id"]]
    field = state["field"]
    if preferred != "STAY":
        direction_length = math.hypot(*preferred_vector)
        target_x = min(
            max(me["x"] + preferred_vector[0] / direction_length * field["width"] * 2, 0),
            field["width"],
        )
        target_y = min(
            max(me["y"] + preferred_vector[1] / direction_length * field["height"] * 2, 0),
            field["height"],
        )
        waypoint_move = _route_move(observation, target_x, target_y, choices, preferred_vector)
        if waypoint_move is not None:
            return waypoint_move

    return max(
        choices,
        key=lambda move: (
            DIRECTION_VECTORS[move][0] * preferred_vector[0]
            + DIRECTION_VECTORS[move][1] * preferred_vector[1],
            move == preferred,
        ),
    )


def _route_move(
    observation: dict[str, Any],
    target_x: float,
    target_y: float,
    choices: list[str],
    preferred_vector: tuple[int, int],
) -> str | None:
    """Use a coarse safe-cell route when a direct move would get trapped."""
    state = observation["state"]
    me = state["players"][observation["player_id"]]
    field = state["field"]
    radius = float(field.get("player_radius", 3.0))
    spacing = 2.0
    max_x = int(field["width"] // spacing)
    max_y = int(field["height"] // spacing)
    obstacles = state.get("obstacles", [])

    def safe_cell(ix: int, iy: int) -> bool:
        x, y = ix * spacing, iy * spacing
        if x - radius < 0 or x + radius > field["width"]:
            return False
        if y - radius < 0 or y + radius > field["height"]:
            return False
        for obstacle in obstacles:
            closest_x = min(max(x, obstacle["x"]), obstacle["x"] + obstacle["width"])
            closest_y = min(max(y, obstacle["y"]), obstacle["y"] + obstacle["height"])
            if math.hypot(x - closest_x, y - closest_y) < radius + 0.25:
                return False
        return True

    safe: set[tuple[int, int]] = {
        (ix, iy)
        for ix in range(max_x + 1)
        for iy in range(max_y + 1)
        if safe_cell(ix, iy)
    }
    if not safe:
        return None

    def nearest_safe(x: float, y: float, search_radius: int) -> tuple[int, int] | None:
        center_x = round(x / spacing)
        center_y = round(y / spacing)
        candidates = (
            (ix, iy)
            for ix in range(max(0, center_x - search_radius), min(max_x, center_x + search_radius) + 1)
            for iy in range(max(0, center_y - search_radius), min(max_y, center_y + search_radius) + 1)
            if (ix, iy) in safe
        )
        return min(candidates, key=lambda cell: (cell[0] * spacing - x) ** 2 + (cell[1] * spacing - y) ** 2, default=None)

    start = nearest_safe(me["x"], me["y"], 2)
    goal = nearest_safe(target_x, target_y, 4)
    if start is None or goal is None or start == goal:
        return None

    def heuristic(cell: tuple[int, int]) -> float:
        dx, dy = abs(goal[0] - cell[0]), abs(goal[1] - cell[1])
        return spacing * (max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy))

    frontier: list[tuple[float, float, tuple[int, int]]] = [(heuristic(start), 0.0, start)]
    costs = {start: 0.0}
    previous: dict[tuple[int, int], tuple[int, int]] = {}
    while frontier:
        _, cost, cell = heapq.heappop(frontier)
        if cost != costs.get(cell):
            continue
        if cell == goal:
            break
        for dx, dy in ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)):
            neighbor = (cell[0] + dx, cell[1] + dy)
            if neighbor not in safe:
                continue
            next_cost = cost + (math.sqrt(2) if dx and dy else 1.0)
            if next_cost >= costs.get(neighbor, math.inf):
                continue
            costs[neighbor] = next_cost
            previous[neighbor] = cell
            heapq.heappush(frontier, (next_cost + heuristic(neighbor), next_cost, neighbor))
    else:
        return None

    route_cell = goal
    while previous.get(route_cell) != start:
        route_cell = previous.get(route_cell)
        if route_cell is None:
            return None
    waypoint_x, waypoint_y = route_cell[0] * spacing, route_cell[1] * spacing

    def move_score(move: str) -> tuple[float, float, bool]:
        vx, vy = DIRECTION_VECTORS[move]
        length = math.hypot(vx, vy)
        next_x = me["x"] + vx / length * float(field.get("player_speed", 4.0))
        next_y = me["y"] + vy / length * float(field.get("player_speed", 4.0))
        waypoint_distance = math.hypot(waypoint_x - next_x, waypoint_y - next_y)
        alignment = vx * preferred_vector[0] + vy * preferred_vector[1]
        return (-waypoint_distance, alignment, move == direction_toward(waypoint_x - me["x"], waypoint_y - me["y"], 0.1))

    return max(choices, key=move_score)


def _simulate_kick(
    observation: dict[str, Any],
    move: str,
    direction: str,
    power: int,
) -> tuple[str | None, tuple[float, float], int]:
    """Estimate a legal kick using the observed arena geometry and official physics."""
    state = observation["state"]
    field = state["field"]
    player_id = observation["player_id"]
    opponent_id = observation["opponent_id"]
    me = state["players"][player_id]
    opponent = state["players"][opponent_id]
    move_x, move_y = DIRECTION_VECTORS[move]
    move_length = math.hypot(move_x, move_y) or 1.0
    player_speed = float(field.get("player_speed", 4.0))
    origin = (
        me["x"] + move_x / move_length * player_speed,
        me["y"] + move_y / move_length * player_speed,
    )
    vector = DIRECTION_VECTORS[direction]
    direction_length = math.hypot(*vector)
    vx = vector[0] / direction_length
    vy = vector[1] / direction_length
    ball_radius = float(field.get("ball_radius", 1.5))
    ball_speed = float(field.get("ball_speed", 8.0))
    kick_distances = field.get("kick_distances", (32.0, 64.0, 96.0))
    remaining = float(kick_distances[power - 1])
    clearance = float(field.get("player_radius", 3.0)) + ball_radius + 0.05
    position = (origin[0] + vx * clearance, origin[1] + vy * clearance)
    velocity = (vx * ball_speed, vy * ball_speed)
    bounces = 0
    sign = 1 if observation["attack_direction"] == "UP" else -1
    goal_left = (field["width"] - field["goal_width"]) / 2
    goal_right = goal_left + field["goal_width"]
    intercept_radius = ball_radius + float(field.get("player_radius", 3.0))
    substep_limit = max(0.25, ball_radius * 0.45)

    while remaining > 1e-9:
        travel = min(ball_speed, remaining)
        substeps = max(1, math.ceil(travel / substep_limit))
        step_distance = travel / substeps
        for _ in range(substeps):
            length = math.hypot(*velocity)
            previous = position
            candidate = (
                previous[0] + velocity[0] / length * step_distance,
                previous[1] + velocity[1] / length * step_distance,
            )
            if (
                goal_left <= candidate[0] <= goal_right
                and (
                    (sign > 0 and candidate[1] + ball_radius >= field["height"])
                    or (sign < 0 and candidate[1] - ball_radius <= 0)
                )
            ):
                return "goal", candidate, bounces

            x, y = candidate
            velocity_x, velocity_y = velocity
            if x - ball_radius < 0 or x + ball_radius > field["width"]:
                velocity_x = -velocity_x
                x = min(max(x, ball_radius), field["width"] - ball_radius)
                bounces += 1
            if y - ball_radius < 0 or y + ball_radius > field["height"]:
                velocity_y = -velocity_y
                y = min(max(y, ball_radius), field["height"] - ball_radius)
                bounces += 1
            velocity = (velocity_x, velocity_y)
            candidate = (x, y)

            for obstacle in state.get("obstacles", []):
                closest_x = min(max(candidate[0], obstacle["x"]), obstacle["x"] + obstacle["width"])
                closest_y = min(max(candidate[1], obstacle["y"]), obstacle["y"] + obstacle["height"])
                if math.hypot(candidate[0] - closest_x, candidate[1] - closest_y) >= ball_radius:
                    continue
                left = obstacle["x"] - ball_radius
                right = obstacle["x"] + obstacle["width"] + ball_radius
                bottom = obstacle["y"] - ball_radius
                top = obstacle["y"] + obstacle["height"] + ball_radius
                crossed_x = previous[0] <= left or previous[0] >= right
                crossed_y = previous[1] <= bottom or previous[1] >= top
                velocity_x, velocity_y = velocity
                if crossed_x:
                    velocity_x = -velocity_x
                if crossed_y:
                    velocity_y = -velocity_y
                if not crossed_x and not crossed_y:
                    velocity_x, velocity_y = -velocity_x, -velocity_y
                velocity_length = math.hypot(velocity_x, velocity_y)
                velocity = (velocity_x, velocity_y)
                candidate = (
                    previous[0] + velocity_x / velocity_length * min(0.05, ball_radius / 10),
                    previous[1] + velocity_y / velocity_length * min(0.05, ball_radius / 10),
                )
                bounces += 1
                break

            position = candidate
            remaining = max(0.0, remaining - step_distance)
            if math.hypot(position[0] - opponent["x"], position[1] - opponent["y"]) <= intercept_radius:
                return "opponent", position, bounces
            if math.hypot(position[0] - origin[0], position[1] - origin[1]) <= intercept_radius:
                return "self", position, bounces
    return None, position, bounces


def _best_kick(observation: dict[str, Any], move: str) -> dict[str, Any] | None:
    """Choose a kick only when it can score or safely advance the ball."""
    state = observation["state"]
    field = state["field"]
    me = state["players"][observation["player_id"]]
    directions = observation["action_space"]["kick"]["direction"]
    powers = observation["action_space"]["kick"]["power"]
    sign = 1 if observation["attack_direction"] == "UP" else -1
    goal_distance_before = field["height"] - me["y"] if sign > 0 else me["y"]
    best_score = 8.0
    best: dict[str, Any] | None = None

    for direction in directions:
        for power in powers:
            outcome, endpoint, bounces = _simulate_kick(observation, move, direction, power)
            goal_distance_after = field["height"] - endpoint[1] if sign > 0 else endpoint[1]
            progress = goal_distance_before - goal_distance_after
            if outcome == "goal":
                score = 1_000_000 - (power - 1) * 10
            elif outcome is not None:
                continue
            else:
                score = progress - bounces * 8
                score -= abs(endpoint[0] - field["width"] / 2) * 0.04
            if score > best_score:
                best_score = score
                best = {"direction": direction, "power": power}
    return best


def _dribble_move(observation: dict[str, Any]) -> str:
    """Carry toward goal, leaning away from nearby pressure when no safe shot exists."""
    player_id = observation["player_id"]
    opponent_id = observation["opponent_id"]
    state = observation["state"]
    me = state["players"][player_id]
    opponent = state["players"][opponent_id]
    field = state["field"]
    sign = 1 if observation["attack_direction"] == "UP" else -1
    dx = field["width"] / 2 - me["x"]
    opponent_dx = opponent["x"] - me["x"]
    opponent_dy = opponent["y"] - me["y"]
    opponent_distance = math.hypot(opponent_dx, opponent_dy)
    if opponent_distance < 22:
        lateral = -1 if opponent_dx >= 0 else 1
        dx += lateral * (22 - opponent_distance) * 1.2
    preferred = direction_toward(dx, sign * field["height"], dead_zone=5.0)
    return _safe_move(observation, preferred)


def tactical_action(observation: dict[str, Any], kick_power: int = 3) -> dict[str, Any]:
    player_id = observation["player_id"]
    opponent_id = observation["opponent_id"]
    state = observation["state"]
    me = state["players"][player_id]
    opponent = state["players"][opponent_id]
    ball = state["ball"]
    attack = observation["attack_direction"]
    sign = 1 if attack == "UP" else -1

    if ball["possession"] == player_id:
        distance_to_goal = state["field"]["height"] - me["y"] if sign > 0 else me["y"]
        opponent_ahead = (
            sign * (opponent["y"] - me["y"]) > 0
            and abs(opponent["x"] - me["x"]) < 12
            and math.hypot(opponent["x"] - me["x"], opponent["y"] - me["y"]) < 55
        )
        side = "LEFT" if opponent["x"] >= me["x"] else "RIGHT"
        dribble = f"{attack}_{side}" if opponent_ahead else attack
        move = _safe_move(observation, dribble)
        if distance_to_goal > 50 and int(ball.get("possession_steps", 0)) < 3:
            return {"move": move}
        direction = dribble if opponent_ahead else direction_toward(
            state["field"]["width"] / 2 - me["x"], sign * distance_to_goal, dead_zone=6.0
        )
        powers = observation["action_space"]["kick"]["power"]
        power = min(max(powers), max(min(powers), kick_power))
        return {"move": move, "kick": {"direction": direction, "power": power}}

    target_x, target_y = ball["x"], ball["y"]
    if ball["status"] == "moving":
        velocity = ball.get("velocity", {})
        target_x += float(velocity.get("x", 0.0))
        target_y += float(velocity.get("y", 0.0))
    elif ball["possession"] == opponent_id:
        defend_sign = -1 if attack == "UP" else 1
        target_y += defend_sign * 3.0
        target_x += -3.0 if opponent["x"] > state["field"]["width"] / 2 else 3.0
    preferred = direction_toward(target_x - me["x"], target_y - me["y"], dead_zone=0.6)
    return {"move": _safe_move(observation, preferred)}


class Policy:
    """Standalone inference policy for the sparse RL models made by train_bot.py."""

    def __init__(
        self,
        q_table: dict[str, list[float]] | None = None,
        visits: dict[str, int] | None = None,
        seed: int = 0,
        evaluation_epsilon: float = 0.03,
        safety_margin: float = 0.6,
        kick_power: int = 3,
    ) -> None:
        self.q_table = q_table or {}
        self.visits = visits or {}
        self.model_seed = seed
        self.evaluation_epsilon = evaluation_epsilon
        self.safety_margin = safety_margin
        self.kick_power = kick_power
        self.random = random.Random(seed)
        self.match_seeded = False

    @classmethod
    def load(cls, path: Path) -> "Policy":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("format") == 3 and raw.get("action_count") == ACTION_COUNT:
            q_table: dict[str, list[float]] = {}
            for key, sparse in raw.get("q_table", {}).items():
                values = [0.0] * ACTION_COUNT
                for index, value in sparse.items():
                    values[int(index)] = float(value)
                q_table[key] = values
            return cls(
                q_table=q_table,
                visits={key: int(value) for key, value in raw.get("visits", {}).items()},
                seed=int(raw.get("seed", 0)),
                evaluation_epsilon=float(raw.get("evaluation_epsilon", 0.03)),
                safety_margin=float(raw.get("safety_margin", 0.6)),
            )
        # The tiny supplied model intentionally selects the tactical fallback.
        return cls(kick_power=int(raw.get("kick_power", 3)))

    @staticmethod
    def state_key(observation: dict[str, Any]) -> str:
        player_id = observation["player_id"]
        opponent_id = observation["opponent_id"]
        state = observation["state"]
        field = state["field"]
        me = state["players"][player_id]
        opponent = state["players"][opponent_id]
        ball = state["ball"]
        width, height = float(field["width"]), float(field["height"])
        sign = 1.0 if observation["attack_direction"] == "UP" else -1.0
        attack_y = me["y"] if sign > 0 else height - me["y"]
        ball_dx, ball_dy = ball["x"] - me["x"], sign * (ball["y"] - me["y"])
        opponent_dx = opponent["x"] - me["x"]
        opponent_dy = sign * (opponent["y"] - me["y"])
        velocity = ball.get("velocity", {})
        nearest = (999.0, 8)
        for obstacle in state.get("obstacles", []):
            dx = obstacle["x"] + obstacle["width"] / 2 - me["x"]
            dy = sign * (obstacle["y"] + obstacle["height"] / 2 - me["y"])
            distance = math.hypot(dx, dy)
            if distance < nearest[0]:
                nearest = (distance, _sector(dx, dy))
        possession = "S" if ball["possession"] == player_id else "O" if ball["possession"] == opponent_id else "F"
        values = (
            min(4, int(me["x"] / width * 5)),
            min(6, int(attack_y / height * 7)),
            _sector(ball_dx, ball_dy),
            _bucket(math.hypot(ball_dx, ball_dy), (7, 16, 32, 60)),
            _sector(opponent_dx, opponent_dy),
            _bucket(math.hypot(opponent_dx, opponent_dy), (8, 18, 38, 70)),
            possession,
            ball["status"][0].upper(),
            _sector(float(velocity.get("x", 0.0)), sign * float(velocity.get("y", 0.0))),
            _bucket(float(ball.get("remaining_kick_distance", 0.0)), (1, 25, 60)),
            _bucket(int(ball.get("possession_steps", 0)), (1, 3, 6)),
            nearest[1] if nearest[0] < 24 else 8,
            _bucket(nearest[0], (8, 16, 24)),
        )
        return "|".join(map(str, values))

    @staticmethod
    def action_from_index(index: int) -> dict[str, Any]:
        if index < len(MOVES):
            return {"move": MOVES[index]}
        kick_index = index - len(MOVES)
        direction = KICK_DIRECTIONS[kick_index // 3]
        return {"move": direction, "kick": {"direction": direction, "power": kick_index % 3 + 1}}

    @staticmethod
    def index_from_action(action: dict[str, Any]) -> int:
        kick = action.get("kick")
        if isinstance(kick, dict) and kick.get("direction") in KICK_DIRECTIONS:
            power = max(1, min(3, int(kick.get("power", 1))))
            return len(MOVES) + KICK_DIRECTIONS.index(kick["direction"]) * 3 + power - 1
        return MOVES.index(action.get("move", "STAY"))

    @staticmethod
    def valid_indices(observation: dict[str, Any]) -> list[int]:
        moves = [index for index in range(1, len(MOVES)) if _move_is_safe(observation, MOVES[index])]
        ball = observation["state"]["ball"]
        if ball["possession"] != observation["player_id"]:
            return moves or [0]
        attack = observation["attack_direction"]
        forward = [attack, f"{attack}_LEFT", f"{attack}_RIGHT"]
        if int(ball.get("possession_steps", 0)) < 2:
            controlled = [MOVES.index(move) for move in forward if _move_is_safe(observation, move)]
            return controlled or moves or [0]
        kicks = [
            len(MOVES) + KICK_DIRECTIONS.index(direction) * 3 + power
            for direction in forward
            for power in range(3)
        ]
        return moves + kicks

    def choose_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        if not self.match_seeded:
            state_seed = int(observation["state"].get("seed", 0))
            side_seed = 17 if observation["player_id"] == "player_1" else 31
            self.random.seed(self.model_seed ^ (state_seed * 1_000_003) ^ side_seed)
            self.match_seeded = True
        fallback_action = tactical_action(observation, self.kick_power)
        valid = self.valid_indices(observation)
        values = self.q_table.get(self.state_key(observation))
        if values is None or self.visits.get(self.state_key(observation), 0) < 2:
            action = fallback_action
        else:
            if self.random.random() < self.evaluation_epsilon:
                action = self.action_from_index(self.random.choice(valid))
            else:
                best = max(values[index] for index in valid)
                fallback = self.index_from_action(fallback_action)
                if fallback in valid and best - values[fallback] < self.safety_margin:
                    action = fallback_action
                else:
                    choices = [index for index in valid if abs(values[index] - best) < 1e-9]
                    action = self.action_from_index(self.random.choice(choices))
        action["move"] = _safe_move(observation, action.get("move", "STAY"))
        if (
            "kick" in action
            and observation["state"]["ball"]["possession"] == observation["player_id"]
        ):
            kick = _best_kick(observation, action["move"])
            if kick is None:
                return {"move": _dribble_move(observation)}
            action["kick"] = kick
        return action
