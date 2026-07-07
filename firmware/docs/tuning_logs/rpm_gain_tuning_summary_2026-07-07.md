# RPM Gain Tuning Summary — 2026-07-07

## Context

- Target hardware: Differential swerve unit firmware on STM32G474 + M3508/C620.
- Important correction: C620 feedback RPM is the M3508 rotor-side RPM before the internal 19:1 reduction.
- Control/kinematics RPM target is the M3508 output-shaft / gearbox-side RPM, so the measured C620 RPM must be divided by 19 at the feedback boundary.
- Previous tuning results taken before this `/19` correction are not valid for final gain selection.

## Current provisional control setup

- C620 feedback scale: `measured_output_rpm = c620_feedback_rpm / 19`
- Drive inner speed PI:
  - `Kp = 5`
  - `Ki = 20` initially
  - `integral_limit = 1200`
- Steer inner speed PI:
  - `Kp = 50`
  - `Ki = 20`
- Steer outer angle loop:
  - `angle_kp = 0.1`
  - `deadband = 0.5 deg`
  - `max_steer_rpm = 0.5`
  - `min_steer_rpm = 0`
  - `accel_limit = 5 rpm/s^2`
- C620 current limit during tests: `2000`

## Acceptance criteria used for point tests

For each target RPM point, judge the final-half steady-state window:

- Mean speed error: `<= max(2 rpm, 5%)`
- Peak-to-peak speed ripple: `<= max(6 rpm, 15%)`
- Steer angle:
  - RMS target: `<= 3 deg`
  - Peak target: `<= 5 deg`
- No motor fault, no runaway, and safe-idle must be flashed/restored after the run.

## Saved results

### 40 rpm point

Run 1:

- Gains: drive `Kp=5`, `Ki=20`
- Test duration: 10 s
- Flash / verify / reset: success
- Safe-idle restore after run: success
- Final-half measured mean wheel RPM: `33.999 rpm`
- Speed peak-to-peak ripple: `243.6 rpm`
- Steer angle peak error: `1.67 deg`
- Result: **FAIL**

Reason:

- Mean speed was below target.
- Ripple was far above the acceptance limit for 40 rpm:
  - Limit: `max(6 rpm, 15%) = 6 rpm`
  - Observed: `243.6 rpm`

Planned next trial:

- Change one variable only: drive `Ki 20 -> 30`
- Keep `Kp=5`
- Repeat the 40 rpm point test.

## Exploratory observations, not final pass/fail results

These were useful for direction but are not formal accepted results:

- Corrected-scale single motor 50 rpm with `Kp=5`, `Ki=20` tracked roughly `47–54 rpm`.
- A relaxed staircase test with loose tolerance (`max(10 rpm, 15%)`) produced:
  - 40 rpm: measured about `41.5 rpm`, angle error about `0.879 deg`
  - 75 rpm: measured about `73.0 rpm`, angle error about `0.615 deg`
  - 150 rpm: run was interrupted before a clean final verdict.
- Earlier exploratory runs suggested 50 / 60 / 75 / 100 / 150 / 250 rpm could run for around 10 s without immediate divergence, but they still need formal point-test verification.

## Workflow notes

- Hardware tests should be serialized by `firmware/scripts/invoke-hardware-session.ps1`.
- Compact serial capture should use `firmware/scripts/compact-test-log.ps1`.
- Each hardware session must restore safe-idle in `finally` before releasing the hardware mutex.
- Results should be appended here or split into per-point log files under `firmware/docs/tuning_logs/`.

## Current state after saved result

- Last known confirmed completed run restored safe-idle successfully.
- The next formal action is the 40 rpm retry with drive `Kp=5`, `Ki=30`.
