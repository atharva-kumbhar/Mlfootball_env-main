# Seed 8206 screenshot and policy experiment

The 1-1 screenshot corresponds to a draw against the bundled Balanced United RL reference. The replay shows that at iteration 231 the reference player (player 2) took possession; after that, its repeated short kicks and same-player interceptions occupied much of the match. Call_of_Duty was player 1 and did not control the ball during that sequence. A submitted agent can legally press for possession, but it cannot change or repair the opponent policy or simulator.

I tested an experimental Call_of_Duty change that rejects predicted self-intercepting/opponent-intercepted kicks and dribbles when it finds no safe forward kick. On seeds 8206-8210, both sides, against the same reference:

| Version | Goals for | Goals against | W-D-L | Action errors |
|---|---:|---:|---:|---:|
| Packaged release | 21 | 12 | 7-3-0 | 0 |
| Experimental anti-self-kick policy | 20 | 14 | 7-1-2 | 0 |

The experiment did not improve the aggregate benchmark, so it was not promoted. The submitted policy was restored from the previously checked release ZIP; its SHA-256 matches the policy in that ZIP. The experiment source is saved as `avoid-selfkick-policy.py` for reference.

This result reinforces that one 1-1 draw does not describe all seeds. The opponent's repeated same-player interceptions are a limitation in the bundled practice opponent, not proof that Call_of_Duty itself is stuck. Do not modify the simulator to alter the opponent; that would violate the competition rules.
