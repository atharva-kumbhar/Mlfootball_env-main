# Call_of_Duty and original starter benchmark

## Test setup

- Opponent: bundled Balanced United RL reference
- Same seeds for both versions: 8600-8604
- Both player sides per seed: 10 matches per version
- Official game configuration was unchanged.
- Scores are from the participant team's perspective.

## Results

| Version | Goals for | Goals against | W-D-L | Action errors |
|---|---:|---:|---:|---:|
| Untouched original starter kit | 20 | 11 | 5-1-4 | 0 |
| Current Call_of_Duty release | 25 | 15 | 5-2-3 | 0 |

On this small matched sample, Call_of_Duty scored 5 more goals and had one fewer loss, but conceded 4 more goals. This is a mixed result, not proof that it will outperform on hidden seeds or against other teams.

The official game ends once either the iteration limit or maximum total-goal limit is reached. A bot cannot guarantee seven goals: the match may end sooner, the opponent may score, and obstacle layouts/seeds vary.

## Training candidates

Additional scoring-reward and curriculum-training candidates were tested, but none has been promoted. The current release remains the release model. Candidate models and the isolated training script are kept under this folder's `experiments/` directory for reference only; do not submit those candidates as the release.

## Integrity and compliance

- The original participant simulator, official game configuration, and starter source were not edited by this work. Validation generated match logs in the original participant folder.
- The official `game.json` SHA-256 remains `ED703234A9CAFC3D06CC1C00D791AEC0DD650E91F3AC12D943A922F5E454C9C0`.
- The current release completed the matched test with zero action errors.
- The current release archive passed `check_submission.py`.
- Current release archive SHA-256: `8ac3bb8a86243e133e8aa673622fe90653547e6c42632dd07f5a9280116dc14e`.
