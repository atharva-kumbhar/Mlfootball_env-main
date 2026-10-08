# Conv-Cup '26 Rulebook and Project Implementation Document

## 1. Source of Rules

The competition rules were taken from the file [Conv-Cup_26_Rulebook.docx.pdf](./Conv-Cup_26_Rulebook.docx.pdf) in the workspace root.

The PDF describes a deterministic 2D soccer AI contest in which:

- exactly two AI-controlled players compete;
- one ball and two opposite goals exist on a rectangular field;
- players move by fixed-speed directional actions;
- the same simulator and fixed environment parameters are used for all teams;
- matches are evaluated head-to-head using random seeds and obstacle layouts;
- outcomes are based on goals scored within the match time and tie-break logic;
- the game engine enforces movement, collisions, possession, kicking, restarts, and goal detection.

The PDF identifies a team event (2-4 participants) and a prize pool. It does **not** specify a double-elimination bracket: it says the exact match count and tournament structure will be announced by the organizers. The PDF says tied matches receive additional iterations under the event tie-break procedure, but does not define that procedure in detail.

## 2. Rulebook Summary

### 2.1 Event flow and competition model

The rulebook states that:

1. Teams register through Unstop.
2. There is an opening ceremony and environment/rules reveal.
3. Teams develop and train with the official simulator.
4. Teams submit agents using the prescribed action interface.
5. Agents compete in evaluation matches using different seeds and obstacle sets.
6. Judging is based on score over the allotted game iterations.
7. In tied scenarios, additional iterations are provided under a tie-break procedure; the PDF does not specify its details.

The project README contains more specific bracket and shootout descriptions than this PDF. Treat those as separate project/organizer documentation, not as rules verified by this PDF, until the organizers confirm they apply.

### 2.2 Core game rules

The official game is a deterministic 2D soccer simulation with:

- two AI-controlled players;
- one ball;
- two opposite goals;
- procedurally generated symmetric obstacles;
- simultaneous action selection for both players;
- physics-based movement, collisions, rebounds, and goal detection;
- automatic possession detection and kick eligibility;
- no fixed goalkeeper role, offside rule, or fouls; the whole field is open.

### 2.3 Gameplay requirements from the rules

The rules emphasize that:

- all teams use the same engine and fixed environment parameters;
- participants may only control their own player through the prescribed interface;
- the agent cannot directly modify the simulator or game engine behaviour;
- both players have equal movement, size, collision, and kicking capabilities;
- the engine updates positions, ball movement, collisions, possession, and goals after both players act simultaneously;
- a moving ball can be intercepted; static obstacles and walls generate reflections;
- obstacle positions are randomized but mirrored around the field center;
- every match is reproducible from the seed and action sequence.

### 2.4 Evaluation and ranking rules

The main evaluation principle is simple:

- multiple matches are used to test generalization;
- different seeds and obstacle layouts are used;
- the primary result is goals scored within the allotted iterations;
- if tied, additional iterations or tie-break procedures decide the outcome.

## 3. What Project Is Implemented

The checked project is an AI soccer participant development kit, not a single agent. It contains:

- a deterministic simulator engine;
- fixed game configuration parameters;
- a starter policy for players;
- a stronger RL-trained policy implementation;
- organizer opponent logic;
- reference baseline bots;
- match runner and viewer tools;
- validation, packaging, and safety checking for submissions;
- training utilities and replay analysis support.

This matches the competition structure and is designed to help participants build and submit their own bots.

## 4. High-Level Architecture

The project is organized under the [participants/](./Mlfootball_env-main/participants) folder. The main components are:

### 4.1 Simulation engine

- [participants/soccer_env/config.py](./Mlfootball_env-main/participants/soccer_env/config.py)
- [participants/soccer_env/engine.py](./Mlfootball_env-main/participants/soccer_env/engine.py)

These files define the official game config and the actual game loop. The engine:

- creates the field, players, and ball;
- validates the configuration constants;
- resets the match to a starting state;
- applies simultaneous movement for both players;
- resolves collisions and contact between players;
- handles possession and tackles;
- launches kicks when a player with possession uses a valid kick action;
- advances ball movement while checking walls, obstacles, and interception;
- detects goals;
- imposes time and goal limits;
- records events for replay and research.

### 4.2 Bot policy logic

- [participants/soccer_env/bots.py](./Mlfootball_env-main/participants/soccer_env/bots.py)
- [participants/reference_bot/policy.py](./Mlfootball_env-main/participants/reference_bot/policy.py)
- [participants/organizer_rl_bot/policy.py](./Mlfootball_env-main/participants/organizer_rl_bot/policy.py)
- [participants/submission_kit/team_bot/policy.py](./Mlfootball_env-main/participants/submission_kit/team_bot/policy.py)

This folder contains the actual decision-making logic. The project contains:

- a tactical baseline action generator;
- an aggressive attacking policy;
- a counter-attacking policy;
- a simple reference bot;
- the organizer RL bot wrapper;
- a starter team bot.

### 4.3 Training and learning layer

- [participants/soccer_env/reinforcement.py](./Mlfootball_env-main/participants/soccer_env/reinforcement.py)
- [participants/train_bot.py](./Mlfootball_env-main/participants/train_bot.py)

These files implement a Q-learning policy for the environment. The system learns a tabular value table over discretized state features. The learner tracks:

- player position in attacking-aligned coordinates;
- ball position and velocity;
- opponent position;
- possession state;
- nearest obstacle information;
- ball remaining kick distance and possession duration.

It chooses among legal actions and updates Q-values after matches or training episodes.

### 4.4 Match orchestration and evaluation

- [participants/soccer_env/match_runner.py](./Mlfootball_env-main/participants/soccer_env/match_runner.py)
- [participants/run_match.py](./Mlfootball_env-main/participants/run_match.py)
- [participants/live_viewer.py](./Mlfootball_env-main/participants/live_viewer.py)
- [participants/replay_viewer.py](./Mlfootball_env-main/participants/replay_viewer.py)

These tools run a full match between agent processes, record JSONL logs, inspect replays, and provide a live viewer. They mirror the contest evaluation flow: a match receives a seed, both players act independently from observations, and the engine produces a deterministic result.

### 4.5 Submission and validation

- [participants/validate_submission.py](./Mlfootball_env-main/participants/validate_submission.py)
- [participants/check_submission.py](./Mlfootball_env-main/participants/check_submission.py)
- [participants/package_submission.py](./Mlfootball_env-main/participants/package_submission.py)

This is the industrial side of the project: it validates that the submission respects the official action protocol, model constraints, file limits, and safety rules expected by the tournament.

## 5. How the Game Works in Detail

### 5.1 Environment constants

The official values are read from [participants/config/game.json](./Mlfootball_env-main/participants/config/game.json):

- field width: 100.0
- field height: 140.0
- goal width: 36.0
- player radius: 3.0
- player speed: 4.0
- ball radius: 1.5
- ball speed: 8.0
- possession radius: 5.0
- kick distances: 32, 64, 96
- obstacle count: 6
- maximum iterations: 400
- maximum goals: 7
- possession timeout: 10 iterations
- loose ball restart timeout: 20 iterations

These parameters are loaded into the GameConfig object and validated before a match begins.

### 5.2 Starting layout

At reset, the engine creates mirrored obstacles using the seed, then places players at the standard kick-off positions:

- player_1 at the lower side of the field;
- player_2 at the upper side of the field;
- the ball starts with the designated initial possessor.

In the project code, the starting positions are set in the engine's _starting_positions() method and the first possessor is defined by config.initial_possessor.

### 5.3 Player actions

Each agent receives an observation object containing:

- match seed;
- current iteration;
- current field metrics;
- positions of both players;
- ball state;
- score;
- obstacles;
- legal action space.

The action contract requires a JSON object like:

```json
{"move":"UP_RIGHT"}
```

or when in possession:

```json
{"move":"UP","kick":{"direction":"UP_LEFT","power":3}}
```

The code normalizes actions in SoccerEnv.normalize_action() and rejects invalid moves or invalid kick directions/powers.

### 5.4 Player movement

The engine computes a proposed move vector from the direction name using a fixed unit-direction table:

- STAY
- UP, UP_RIGHT, RIGHT, DOWN_RIGHT
- DOWN, DOWN_LEFT, LEFT, UP_LEFT

The move is applied with fixed player speed. The move is rejected if it would exceed field boundaries or hit an obstacle. If both players attempt to occupy nearly the same location, the engine resolves contact by separating them instead of allowing indefinite deadlock.

### 5.5 Possession and tackling

After movement, if a player has possession:

- the system checks for a tackle attempt by the opponent;
- a new challenge can steal the ball if the challenger is close enough and moving;
- a newly won ball receives a brief protected dribble period before being eligible for a tackle;
- if the player keeps possession too long, the engine automatically releases the ball toward the attacking goal.

This logic appears in _resolve_tackle() and the possession timeout handling inside step().

### 5.6 Kicks and ball physics

When a player in possession sends a kick action:

- the player releases the ball from their position plus a clearance offset;
- a velocity is assigned based on the chosen direction and configured ball speed;
- a kick has a finite travel distance from the configured kick_distances list;
- the ball continues moving until it either reaches the goal, bounces, is intercepted, or stops.

The engine resolves the ball in _move_ball(), which steps the ball with sub-steps, checks for goal conditions, wall bounces, obstacle bounces, and interceptions. A ball that stops is flagged as stationary and can later be reclaimed or restarted.

### 5.7 Goal detection and scoring

A player scores when the ball crosses the goal line inside the central goal opening.

The project uses a goal check in _goal_scorer():

- if the ball enters the central goal opening at the top wall, player_1 scores;
- if it enters the central goal opening at the bottom wall, player_2 scores;
- the match score is updated immediately;
- the conceding side restarts with the next kickoff.

### 5.8 Restarts and anti-stall logic

The engine includes recovery logic for several special situations:

- after goals, the conceding player receives the next possession restart;
- when the ball is loose and unclaimed for too long, it is dropped to center;
- possession timeouts release the ball toward the attacking goal;
- stalled loose-ball states are detected and restarted to prevent dead matches.

This is implemented in _restart(), _restart_stalled_loose_ball(), and the possession timeout section of step().

### 5.9 Obstacles and deterministic play

Obstacle generation is handled by _generate_obstacles(). It:

- creates mirrored rectangles across the field centre;
- ensures they do not collide with starting positions or each other;
- keeps them static during the match;
- uses the seed to generate a repeatable layout.

Ball collision with obstacles is handled in _bounce_from_obstacles(), and player collision with obstacles is checked in _valid_player_position().

## 6. Project Implementation Behaviour

### 6.1 Starter bot behaviour

The starter tactical policy in [participants/submission_kit/team_bot/policy.py](./Mlfootball_env-main/participants/submission_kit/team_bot/policy.py) behaves like this:

- if the bot has the ball, it tries to advance toward the opponent goal;
- it avoids obstacles when choosing a move;
- it does not immediately over-kick from a safe possession state;
- if a defender is near, it dribbles around the defender or shoots at goal;
- if the ball is loose or moving, it tracks the ball with a lead prediction;
- if the opponent has the ball, it presses from the goal side to contest possession.

This is a reliable hand-coded baseline rather than a deep strategy engine.

### 6.2 Aggressive and counter policies

The environment's bot module includes multiple tactical styles:

- practice_action: balanced tactical fallback
- aggressive_action: more direct attacking press and shot pressure
- counter_action: stronger goal-side and counter-attacking behaviour

These are used for curriculum training and as stronger baselines against RL learners.

### 6.3 Reinforcement learning model

The RL policy in [participants/soccer_env/reinforcement.py](./Mlfootball_env-main/participants/soccer_env/reinforcement.py):

- discretizes game state into a compact key;
- builds a Q-table from state features;
- learns movement and kick actions;
- suppresses illegal or low-value actions using valid-action masking;
- uses a safety fallback to a tactical policy when Q-values are weak or untrained;
- saves the learned model in a sparse JSON format.

This project therefore implements a classic tabular RL approach rather than a neural network or full game-theory solver.

### 6.4 Organizer opponent

The project includes an organizer RL bot in [participants/organizer_rl_bot](./Mlfootball_env-main/participants/organizer_rl_bot). The README describes it as the actual Balanced United RL opponent, and the model path under [participants/organizer_rl_bot/models](./Mlfootball_env-main/participants/organizer_rl_bot/models) is the official tournament-ready model.

This opponent is used for tournament-style evaluation and for training a competitor against the strongest provided baseline.

### 6.5 Match protocol implementation

The runner in [participants/soccer_env/match_runner.py](./Mlfootball_env-main/participants/soccer_env/match_runner.py) runs the external-process protocol:

- each bot gets an observation via stdin JSON line;
- the bot responds with exactly one JSON action line to stdout;
- action timeouts, malformed responses, oversize responses, or process failures are treated as `STAY` and counted as action errors;
- the engine records logs per iteration in JSONL format;
- matches can be replayed from those logs.

This is important because the competition rules require a strict submission interface, and the implementation actively enforces it.

## 7. What Is Already Implemented vs. Not Implemented

### Implemented

- full deterministic 2D soccer game environment;
- player and ball movement rules;
- obstacle generation and collision response;
- possession, kicking, blocking, and interception logic;
- scoring and restart logic;
- training and evaluation toolkit;
- RL and handcrafted baselines;
- submission validation, packaging, and static safety checks;
- viewer and replay infrastructure.

### Not fully implemented in the codebase

The kit behaves like a competition simulator and development environment, but it does not appear to implement the entire public tournament administration stack, such as:

- a full prize/leaderboard system;
- a live bracket manager with double-elimination scheduling;
- a public multi-team web dashboard;
- a complete official event registration backend;
- player identity and team credential management beyond local submission files.

These are competition-organizer concerns rather than game-simulation concerns; the project focuses on the game engine and participant training pipeline.

## 8. How the Project Aligns with the Rulebook

The project is strongly aligned with the rulebook:

- the same one-ball/two-player structure is used;
- simultaneous action selection is implemented;
- possession, kick eligibility, and collisions are enforced;
- obstacles are mirrored and random-seeded;
- scoring and restart logic are present;
- match reproducibility through seed and action sequence is supported;
- evaluation by multiple seeds and layouts is built into the trainer and match runner.

The project is therefore a practical implementation of the rules described in the PDF, with training and submission tooling layered around the core game engine.

## 9. Practical Explanation of the Game Loop

At a high level, the loop is:

1. Start a match with a seed and obstacle layout.
2. Send each player their local observation.
3. Each player chooses a move and optional kick.
4. Move both players simultaneously.
5. Resolve contact and tackle conditions.
6. If a player has possession, let them kick or force a release after timeout.
7. Advance the ball and resolve walls, obstacle reflections, and interceptions.
8. Check whether a goal was scored.
9. Restart if needed, then continue until the match limit or win condition is reached.

This loop is implemented in the step() method of the SoccerEnv class.

## 10. Final Interpretation

This project is a complete AI-soccer competition toolkit. It is not just a simple game; it is a training, evaluation, and submission environment built around a deterministic simulator.

The strongest way to think about it is:

- the rulebook defines the competition rules;
- the engine implements those rules physically;
- the bot policies implement the strategy layer;
- the training code learns better strategy over many matches;
- the validation and packaging tooling makes the system ready for real tournament submission.

That makes the project a full lifecycle environment for building competitive AI soccer agents.
