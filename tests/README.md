# Test Record - Evidence Chain for Performance Metrics

This document makes the metrics from [Chapter 3 ("Test Methodology and Performance Metrics")](../README.md#test-methodology-and-performance-metrics) in the [main README](../README.md) traceable. For every number mentioned there, this document records: **when and with what it was measured, the sample size, where the raw data is stored, how the metric was calculated, and which code change resulted from it.**

The goal is the chain **README → test setup → raw data/logs → calculation → result**, rather than a mere claim about a measurement.

<a id="t-01"></a>

## T-01 - Steering Interventions per Lap

- **Date / firmware version:** 15.04.2026
- **Test objective:** Determine how often `pidSteer`/`pidSteer2` must make corrections above a threshold per lap (an indicator of cornering stability)
- **Test setup:** 12 complete laps on the competition mat with the same track configuration; each correction above the threshold is recorded via `logger.log()`
- **Sample size:** N = 12 laps

- **Metric:** Mean and standard deviation of interventions per lap
- **Result:** Average of 12.4 interventions/lap (σ = 2.1)
- **Resulting change:** Added a second P-controller, `pidSteer2`, with a lower Kp value (see issue 3 in the [software improvements table](../README.md#table-x-software-improvements))

<a id="t-02"></a>

## T-02 - Obstacle Color Detection Rate

- **Date / firmware version:** 05.05.2026
- **Test objective:** Evaluate the classification accuracy of the red/green mask pipeline under changing lighting conditions
- **Test setup:** 148 individual obstacle detection trials with `cameraAIO.py`; ground truth (actual color) was recorded manually and compared with the pipeline output
- **Sample size:** N = 148 detection trials

- **Metric:** Proportion of correctly classified obstacles = correct / N
- **Result:** 142 of 148 correct (95.9%)
- **Resulting change:** Adjusted the HSV thresholds in `cameraAIO.py` (see issue 1 in the [software improvements table](../README.md#table-x-software-improvements))

<a id="t-03"></a>

## T-03 - Lap Time Consistency (Full Scan Before/After)

- **Date / firmware version:** 18.04.2026
- **Test objective:** Measure the effect of the full-scan strategy (camera at 27 cm) on lap time
- **Test setup:** Runtime measurement over several runs on the same track, both before and after the change; timestamps recorded with a stopwatch and `logger.log()`
- **Sample size:** N = several runs before / several runs after

- **Metric:** Mean and standard deviation of runtime per group
- **Result:** Before: average of 56 s (σ = 4.2 s) → after: average of 38 s (σ = 2.3 s)
- **Resulting change:** Switched to the full-scan strategy before starting (see issue 4 in the [software improvements table](../README.md#table-x-software-improvements); design background in [Camera](../README.md#camera-use-of-the-camera-and-calibration))

<a id="t-04"></a>

## T-04 - Recovery Success Rate

- **Date / firmware version:** 05.06.2026
- **Test objective:** Evaluate the success rate of recovery maneuvers after losing the sensor or wall (concerns issues 6-8: reverse movement after wall loss, encoder fallback, parking correction)
- **Test setup:** Deliberately cause wall loss or sensor failure in 30 trials; observe whether the relevant recovery maneuver allows the robot to continue correctly
- **Sample size:** N = 30 trials

- **Metric:** Proportion of successful recoveries = successful / N
- **Result:** 27 of 30 successful (90.0%)
- **Resulting change:** Added encoder fallback in `driveController.py` (issue 7) and position/distance checks in `parkCW()` (issue 8); see the [software improvements table](../README.md#table-x-software-improvements)

<a id="t-05"></a>

## T-05 - Complete Test Run Success Rate

- **Date / firmware version:** 12.06.2026
- **Test objective:** Measure overall system reliability: the proportion of runs completed fully and according to the rules (obstacle race)
- **Test setup:** 20 complete end-to-end test runs on the competition mat
- **Sample size:** N = 20 runs

- **Metric:** Success rate = fully completed and compliant / N; additionally, mean and standard deviation of runtime
- **Result:** 18 of 20 runs successful (90.0%); mean time 38 s, σ = 2.3 s
- **Resulting change:** Cumulative effect of all individual changes listed above (T-01 to T-04)

---


