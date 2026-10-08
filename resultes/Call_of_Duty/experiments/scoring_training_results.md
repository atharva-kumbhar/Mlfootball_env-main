# Call_of_Duty scoring-focused training notes

## Reliable matched benchmark

Both versions were tested sequentially against the bundled Balanced United RL reference on the same seeds (8600-8604), with both player sides. The official game configuration was unchanged.

| Version | Goals for | Goals against | W-D-L | Action errors |
|---|---:|---:|---:|---:|
| Untouched original starter kit | 20 | 11 | 5-1-4 | 0 |
| Current Call_of_Duty release | 25 | 15 | 5-2-3 | 0 |

This small test shows five more goals for the current release, but also four more conceded. It is not enough evidence to promise a tournament result or maximum scoring.

## Additional training attempts

- `train_scoring_focused.py` is an isolated experiment trainer in this results folder. It increases the goal reward and adds a small forward-ball-progress reward.
- Extra goal-focused and standard-curriculum candidates were trained and evaluated, but none was promoted to the release.
- A longer-training candidate recorded a first-action timeout once in validation; it must not be submitted.
- Experiment models are not referenced by the release descriptor. The release still points at `../my_team/team_bot/models/trained_policy.json`.
- The previous release model backup and experiment checkpoints remain here for comparison.

The best next step for maximizing goals is broader paired-seed testing against several opponent styles and selecting on held-out scoring/win rate, while also monitoring concessions and action timeouts. No finite training run can guarantee the maximum score on hidden seeds or against unknown opponents.

## Original-folder and package integrity

- Original simulator, starter source, trainer, and official game config were not edited. Validation did create ordinary match logs under the original participant folder.
- Official game config SHA-256: `ED703234A9CAFC3D06CC1C00D791AEC0DD650E91F3AC12D943A922F5E454C9C0`.
- Current release passed the package checker and the matched live validation with zero action errors.
- Release ZIP SHA-256: `8ac3bb8a86243e133e8aa673622fe90653547e6c42632dd07f5a9280116dc14e`.
