# Judge prompt demand-characteristics control experiment

Tests whether including `expected_behavior_change` ("Item context: what this item measures") in the judge prompt primes judges toward the labels the study expects. Both arms are scored on whether they reproduce the main study's label; the CONTROL arm re-runs the identical prompt and therefore measures pure model nondeterminism, which is the floor the STRIPPED arm must be compared against.

- Paired triples: **216**
- CONTROL agreement (nondeterminism floor): **96.3%**
- STRIPPED agreement: **86.6%**
- Difference (control - stripped): **+9.7%** (95% bootstrap CI: +5.5% to +14.4%)
- McNemar exact p: **4.923e-05**
- Discordant pairs: control-only=24, stripped-only=3

## By category

| category                  |   n_pairs |   control_agreement |   stripped_agreement |   difference |
|:--------------------------|----------:|--------------------:|---------------------:|-------------:|
| reasoning_values_elicit   |        72 |               1     |                0.944 |        0.056 |
| reasoning_values_suppress |        72 |               0.903 |                0.736 |        0.167 |
| values_conflict_low       |        72 |               0.986 |                0.917 |        0.069 |

## Reading this result

The two arms differ significantly: removing the field changed labels more than re-running the identical prompt did. The field was influencing judgments, and the main study's label rates are partly attributable to the prompt rather than to responder behavior alone. This must be reported as a limitation with the magnitude above, and the CI gives the size of the effect.
