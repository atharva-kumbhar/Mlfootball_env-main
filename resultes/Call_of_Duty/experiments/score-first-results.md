# Call_of_Duty score-first strategy results

## Objective

The strategy prioritizes the number of goals Call_of_Duty scores, rather than maximizing win rate. It carries toward the attacking goal when the state does not present a predicted goal opportunity, selects legal forward/scoring kicks, and presses the carrier when defending. It continues to use only the official observation/action interface; it does not change the simulator, opponent, or official game configuration.

## Paired benchmark

Tested against Balanced United RL Reference on the same ten seeds (8206-8215), with each seed played once on both player sides: 20 matches per version. This is a small deterministic test set, not a prediction for unknown tournament opponents.

| Version | Goals for | Goals against | Goal difference | W-D-L | Action errors |
|---|---:|---:|---:|---:|---:|
| Previous release | 48 | 20 | +28 | 14-4-2 | 0 |
| Score-first strategy | 57 | 27 | +30 | 12-1-7 | 0 |

The new strategy scored 9 more goals and had a 2-goal better aggregate difference, but won 2 fewer matches and conceded 7 more. This is a real goals-for improvement on these seeds, not an across-the-board performance improvement. It was selected because the requested priority is scoring more goals. Results also varied by seed and side.

For seeds 8206-8210, it scored 23 versus 21 for the previous release. For seeds 8211-8215, it scored 34 versus 27.

## Release verification

- The final release descriptor uses team name `Call_of_Duty` and the existing trained JSON model.
- The current source simulator/configuration was not changed.
- Participant smoke tests pass.
- Both-side validation of the promoted release on seed 8206 reported zero action errors.
- Official archive checker: PASS.
- Final archive SHA-256: `2e3cd11e3d58779379f72005398b2b7ff29328e92349f9ca3a2d7f1dbae71a63`.

The promoted release is `../my_team/`; packaged archive: `../Call_of_Duty.zip`. The previous policy is backed up as `./pre-score-first-policy.py`.
