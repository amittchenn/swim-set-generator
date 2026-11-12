
# Swim Workout Vocabulary

This document defines the standardized vocabulary, schema conventions, and validation rules for swim workout JSON files.

## 1. Practice-Level Fields

### date

- Format: `YYYY-MM-DD`
- Example: `2026-10-28`

### group

Identifies the training group.

Allowed values:
- `competitive` — Comp, Competitive
- `sprint` — Comp Sprint, Sprint
- `distance` — Mid/Distance, Comp Distance, Distance, Mid-D
- `intermediate` — Inter, Intermediate
- `intro` — Intro
- `mixed` — Whole-team or special-day groups: Swim Out, Everyone Else, Non-Meet Swimmers, Meet Prep
- `recreational`
- `masters`
- `developmental`

Additional groups must be added to the vocabulary before use.

All values use lowercase snake_case.

### focus

Describes the primary training objective.

Allowed values:
- `recovery` — Low-intensity training focused on recovery
- `endurance` — Aerobic conditioning and sustained swimming
- `speed` — Sprinting and maximum-speed development
- `technique` — Stroke mechanics and skill development
- `race_pace` — Swimming at target competition speeds
- `lactate_tolerance` — High-intensity repeats with long rest to build tolerance to lactate

Use at most one focus per practice. Use `null` if the practice doesn't state a focus.

### phase

Describes the season training phase.

Allowed values:
- `base` — Aerobic foundation and general conditioning
- `build` — Increasing training intensity and specificity
- `taper` — Reduced volume before competition
- `null` — Unknown or unspecified

The phase belongs at the practice level, not the set level.

### unit

Defines the distance measurement used throughout the practice.

Allowed values:
- `yards`
- `meters`

Rules:
- Every distance in a practice uses the specified unit.
- Do not mix yards and meters within one practice.
- Do not automatically convert distances.
- If the pool or workout unit is unknown, confirm it before importing.

### total_distance

- Positive integer: the total the **coach wrote** for the practice.
- `null` if the coach did not state a total.
- Measured in the practice-level `unit`.
- Never filled in by hand from a computed sum. The validator computes sums itself.

Use `total_distance` instead of `total_yards` to support both yards and meters.

---

## 2. Set-Level Fields

### name

The coach's original set name.

Examples:
- `Warm Up`
- `Pre Set - Kick`
- `WD`
- `Warm Down`

Names are preserved exactly as written.

### category

Allowed values:
- `warmup`
- `preset`
- `main`
- `kick`
- `cooldown`

Rules:
- `warmup`: the first set, usually named Warm Up.
- `preset`: any set between the warmup and the main set (Pre-Set, Turn Work, drill or technique sets).
- `main`: the set the coach calls Main, or the hardest/longest set of the practice. Sets after it that aren't cooldown are also `main`.
- `kick`: a set that is entirely kick.
- `cooldown`: Warm Down, WD, Cool Down.

### set_distance

- Positive integer: the set distance the **coach wrote**.
- `null` if the coach did not state one.
- Measured in the practice-level `unit`.
- Includes all repetitions and nested rounds.

### reps

- Positive integer.
- Number of times the entire set is repeated.

### items

- Ordered array of swimming items or nested rounds.
- Array order must preserve the actual swimming sequence.

---

## 3. Item-Level Fields

### reps

- Positive integer representing the number of repetitions.

### distance

- Positive integer representing the distance of one repetition.
- Uses the practice-level `unit`.
- `null` when the board gives no distance (e.g. bungee work, "4 HVO").
- Omitted for nested rounds.

### stroke

Allowed values:
- `free` — Freestyle
- `back` — Backstroke
- `breast` — Breaststroke
- `fly` — Butterfly
- `im` — Individual medley
- `choice` — Swimmer's choice or unspecified stroke
- `null` — Only allowed inside a nested round that sets `stroke_rotation`

### stroke_rotation

Set on a nested round when the stroke changes each round.

Allowed values:
- `im_order` — Round 1 fly, round 2 back, round 3 breast, round 4 free
- `null` — No rotation

Example: `500 (100 drill, 25 swim IMO)` is a round with `reps: 4`, `stroke_rotation: im_order`, and children with `stroke: null`.

Normalization:
- `FR`, `Free`, `Freestyle` → `free`
- `BK`, `Backstroke` → `back`
- `BR`, `Breaststroke` → `breast`
- `FL`, `Butterfly` → `fly`
- `IM` → `im`
- `CH`, `Choice` → `choice`

### type

Allowed values:
- `swim` — Normal swimming
- `kick` — Kick-focused activity
- `drill` — Technique drill or named drill
- `pull` — Pull-focused activity
- `scull` — Sculling activity
- `null` — Mixed or unclear activity (explain in `notes`)

Rules:
- If `drill` is not `null`, `type` must be `drill`.
- Turn practice (single/double turn reps) uses `type: drill`.
- `type: pull` does not automatically imply use of a pull buoy.
- Equipment is specified independently in `equipment`.
- A pull set may use paddles, a buoy, both, or neither.

---

## 4. Timing Fields

### interval_seconds

- Positive integer representing the send-off interval in seconds.
- `null` if no send-off interval is specified.

Examples:
- `:55` → `55`
- `1:05` → `65`
- `1:35` → `95`
- `1:40` → `100`
- `2:00` → `120`
- `4:20` → `260`

A send-off interval includes swimming time and any remaining rest.

### rest_seconds

- Nonnegative integer representing prescribed rest after each repetition.
- `null` if no rest-based instruction is specified.

Example:

```json
{
  "reps": 4,
  "distance": 100,
  "interval_seconds": null,
  "rest_seconds": 15
}
```

Interpretation:
- Swim 100.
- Rest 15 seconds.
- Repeat for four repetitions.

### Timing validation

Each item must use at most one timing method.

Valid:
- `interval_seconds: 100`, `rest_seconds: null`
- `interval_seconds: null`, `rest_seconds: 15`
- Both fields `null`

Invalid:
- `interval_seconds: 100`, `rest_seconds: 15`

Rules:
1. Both timing fields may be `null`.
2. Both timing fields must never contain numeric values simultaneously.
3. Send-off intervals are measured from one repetition's start to the next.
4. Rest-based intervals specify recovery time independent of swimming speed.
5. Rest after the final repetition is not assumed unless explicitly specified.

---

## 5. Equipment Vocabulary

### equipment

An array of standardized equipment values.

Allowed values:
- `fins`
- `paddles`
- `snorkel`
- `pull_buoy`
- `kickboard`
- `bungee` — Resistance cord tied to the waist; work until it stops you, then hold for a few strokes. Distance is usually `null`.
  - `type` follows the activity: bungee kick → `kick`, arms-only bungee work → `pull`, full stroke → `swim`.
  - "Bungee pull" means a resisted full-stroke sprint → `type: swim`.

Examples:

No equipment:

```json
"equipment": []
```

Pull buoy and paddles:

```json
"equipment": ["pull_buoy", "paddles"]
```

Snorkel and fins:

```json
"equipment": ["snorkel", "fins"]
```

Rules:
1. Always use an array, including when no equipment is specified.
2. An empty array means no equipment is prescribed.
3. Equipment values must match the allowed vocabulary.
4. Do not include duplicate equipment values.
5. Equipment is independent of `stroke` and `type`.
6. `type: pull` does not require `pull_buoy`.
7. `type: kick` does not require `kickboard`.
8. Never infer equipment solely from the activity type.
9. New equipment must be added to this vocabulary before use.

---

## 6. Drill Vocabulary

### drill

Allowed values:
- `dressel`
- `over_under`
- `tiger_tumble`
- `tallahassee_tumble`
- `null`

Definitions:
- `dressel` — Dressel Drill
- `over_under` — Over/Under
- `tiger_tumble` — Tiger Tumble
- `tallahassee_tumble` — Tallahassee Tumble
- `null` — No named drill

Rules:
- Named drills require `type: drill`.
- Generic technique work may use `type: drill` with `drill: null`.
- New drill names must be normalized and documented.

---

## 7. Effort Vocabulary

### effort

Allowed values:
- `easy`
- `social`
- `speed_play`
- `descend`
- `hvo`
- `null`

Definitions:
- `easy` — Relaxed, low-intensity swimming
- `social` — Conversational effort
- `speed_play` — Varying speed
- `descend` — Increasing speed across repetitions
- `hvo` — High velocity overload: short all-out sprints of about 5-10 seconds. Usually timed, so `distance` is often `null`.
- `null` — No specified effort

Rules:
- Do not encode repetition counts inside effort labels.
- Use `descend`, not `descend_1_3`.
- The `reps` field describes the repetition count.

---

## 8. Breathing Vocabulary

### breathing

Allowed values:
- `count`
- `no_breath`
- `null`

### breathing_pattern

Allowed values:
- Array of positive integers
- `null`

### pattern_per

- Positive integer representing the distance assigned to each breathing-pattern value.
- `null` when no distance-based pattern applies.
- Measured in the practice-level `unit`.

Example:

```json
{
  "reps": 3,
  "distance": 100,
  "breathing": "count",
  "breathing_pattern": [4, 3, 2, 1],
  "pattern_per": 25
}
```

Interpretation for each 100:
- First 25: breathing count 4
- Second 25: breathing count 3
- Third 25: breathing count 2
- Fourth 25: breathing count 1

Repeat the pattern for each repetition.

Validation:
- `breathing: count` requires `breathing_pattern` and `pattern_per`.
- The pattern restarts for each repetition.
- The pattern repeats within a repetition, so the distance must be a multiple of the pattern length:

`distance % (length(breathing_pattern) * pattern_per) == 0`

Example: `400 breathe 3-5-3-7 by 50` → `distance: 400`, `breathing_pattern: [3, 5, 3, 7]`, `pattern_per: 50` (pattern runs twice).

- When `breathing` is `null`, both pattern fields must be `null`.

---

## 9. Start Vocabulary

### start

Allowed values:
- `off_blocks`
- `null`

Definitions:
- `off_blocks` — Start from starting blocks
- `null` — No specified starting instruction

Starting instructions belong in `start`, not `effort`.

Normalization:
- `dive`, `OTB`, `off the block(s)`, `starts` → `off_blocks`

---

## 10. Notes

### notes

Free-text field reserved for instructions that cannot be represented by standardized fields.

Examples:
- Unusual coach instructions
- Unrecognized abbreviations
- Complex activity combinations
- Clarifications requiring human review

Use `null` when unnecessary.

Do not duplicate information already represented by structured fields.

---

## 11. Nested Rounds

Nested rounds preserve the exact sequence of alternating activities.

Each nested round contains:
- `reps`
- `items`

Example: 200 IM Kick/Drill by 50

```json
{
  "reps": 2,
  "items": [
    {
      "reps": 1,
      "distance": 50,
      "stroke": "im",
      "type": "kick"
    },
    {
      "reps": 1,
      "distance": 50,
      "stroke": "im",
      "type": "drill"
    }
  ]
}
```

Actual sequence:
1. 50 IM kick
2. 50 IM drill
3. 50 IM kick
4. 50 IM drill

Distance:

`2 * (50 + 50) = 200`

Do not flatten alternating activities into grouped totals if doing so changes their order.

### Round shorthand

- `2 x { ... }` → a round with `reps: 2` containing the items inside the braces.
- `8 x 25 speed play x2` → a round with `reps: 2` containing `8 x 25`. A trailing `xN` repeats the whole line N times.

---

## 12. Distance Validation

For a normal item:

`item_distance = reps * distance`

For a nested round:

`round_distance = reps * sum(child_distances)`

For a set:

`computed_set = reps * sum(item_distances)`

For the complete practice:

`computed_total = sum(computed_sets)`

All calculations use the practice-level `unit`. Computed values are never stored in the file.

### Checking against stated distances

| Situation | Result |
|---|---|
| All distances known, matches stated value | ✅ pass |
| All distances known, does not match stated value | ❌ error |
| Some item distances `null` | ⚠️ warning: cannot verify |
| Stated value is `null` | skip comparison |

### Example

| Set | Distance |
|---|---:|
| Warm up | 600 |
| Pre-set | 1000 |
| Main set | 1500 |
| Warm-down | 400 |
| Total | 3500 |

The Main set has `reps: 3`, so its distance is 3 × its items.

---

## 13. General Validation Rules

1. Dates must use `YYYY-MM-DD`.
2. `group` must use the approved lowercase vocabulary.
3. `focus` must use the approved lowercase vocabulary.
4. `phase` must be `base`, `build`, `taper`, or `null`.
5. `unit` must be `yards` or `meters`.
6. `phase`, `focus`, and `unit` belong at the practice level.
7. `stroke` must match its approved vocabulary.
8. `type` must match its approved vocabulary.
9. `category` must match its approved vocabulary.
10. `effort` must match its approved vocabulary.
11. Named drills must match the approved drill vocabulary.
12. Named drills require `type: drill`.
13. `interval_seconds` and `rest_seconds` cannot both be numeric.
14. `equipment` must be an array of approved values.
15. Equipment must not be inferred from activity type.
16. Repetitions and distances must be positive integers.
17. Nested rounds must preserve workout order.
18. Breathing patterns must specify their distance granularity.
19. Stated `set_distance` must match the computed distance when every item distance is known.
20. Stated `total_distance` must match the computed total when every distance is known.
21. All distances use the same practice-level unit.
22. Missing or uncertain information should not be guessed.
23. Unknown abbreviations should be verified before normalization.
24. Standardized labels must use lowercase snake_case.
25. Each file contains exactly one practice object (no outer list).

---

## 14. Extending the Vocabulary

When importing new practices:

1. Attempt to map each instruction to an existing standardized value.
2. Avoid creating synonyms for existing values.
3. Add a new canonical value only when necessary.
4. Document its meaning in this file.
5. Update the validator to accept the new value.
6. Preserve uncertain instructions in `notes` until verified.
7. Do not silently convert units or infer equipment.

The goal is consistent, structured, machine-readable training data that can be validated, analyzed, and used for workout generation.
