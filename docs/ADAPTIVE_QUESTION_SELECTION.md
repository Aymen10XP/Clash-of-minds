# Adaptive Question Selection

## What the feature does

Online Top Score practice now records a selection strategy for each run and chooses each next question near a target predicted success probability of 70%. It samples from up to three similarly suitable unused questions instead of repeating a fixed easiest-to-hardest sequence. A 10% randomized control group retains the old uniform choice so later results can be compared with adaptive runs.

When a compatible trained checkpoint is installed, the app uses a small CPU-friendly PyTorch neural network. The network combines a learned topic embedding with question difficulty, the player's historical overall and topic accuracy, response time, response counts, and the question's historical accuracy. Predictions are used only for selection; answer correctness and scoring remain server-authoritative.

Without PyTorch or a trained checkpoint, the app uses a smoothed history-based probability estimate. With little personal history, difficulty priors keep the experience usable and favor a moderate challenge. The API and game screen identify randomized, history-based, neural, and offline runs separately. Offline practice keeps its existing local selection because no server-side model is available there.

## Data and model safeguards

- Training reads saved `TopScoreResponse` records from `random_control`, `history`, and `neural` runs. It does not invent examples or use a generated dataset.
- Each training row uses only answers recorded before that response, including prior overall/topic performance, average response time, and question history.
- The trainer requires at least 200 eligible responses and 8 players by default. It refuses to save a model below either threshold.
- Validation uses the latest 20% of responses in time order. It reports Brier score, threshold accuracy, mean predicted accuracy, and actual accuracy beside the history baseline.
- `selection_mode` distinguishes new baseline/adaptive runs and preserves existing runs as `legacy`. Offline synced runs are marked `offline` and excluded from training and cohort reports.
- A checkpoint is a local deployment artifact at `var/adaptive_question_model.pt` by default. It is not committed; train it from the target database's real gameplay history.
- The control group and observed cohort metrics support evaluation, but small or non-randomly retained player histories do not prove that adaptation improves learning.

## Install and train

PyTorch is optional; the normal application and history fallback do not require it. Install the optional ML dependency in the activated project environment:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```

The current question set and response history may not meet the minimum. The trainer reports the available count and exits without creating a checkpoint until enough real history exists.

```powershell
.venv\Scripts\python.exe manage.py train_adaptive_model --settings=server.settings
```

Use `ADAPTIVE_MODEL_PATH` to choose another checkpoint path and set the same variable for the running Django process. `ADAPTIVE_RANDOM_CONTROL_RATE` sets the randomized comparison share; it defaults to `0.10` and is clamped to 0–1.

## Evaluate prediction quality and game outcomes

The training command compares the trained network against the history-based predictor on a chronological holdout. Lower Brier score is better calibrated. Check that predicted mean accuracy is close to actual accuracy as well as the classification threshold result; a single accuracy number is not enough to assess probability estimates.

After at least 30 runs per group have accumulated, report actual response accuracy and completion rate for each recorded group:

```powershell
.venv\Scripts\python.exe manage.py evaluate_adaptive --settings=server.settings
```

The report shows run count, response count, mean per-run accuracy, overall response accuracy, and completion rate (`finished` runs divided by all runs in that group). If a group has fewer than 30 runs, it is explicitly marked too small to interpret. Compare `history` and `neural` with `random_control`; report group sizes and dates, and do not claim improvement unless the observed outcomes support it. For stronger evidence, keep the comparison period long enough to reduce random variation and compare player cohorts over the same period.

## Limitations

The project has a small question catalog and likely few real response examples. Until the trainer accepts enough real data and validation improves over the history baseline, the neural checkpoint is not active; the game uses the history fallback. Even a successful chronological holdout does not establish that players learn more or abandon less. That requires a larger, representative live cohort and a controlled comparison of accuracy and completion outcomes.

For PyTorch installation commands and platform-specific wheels, use the [official PyTorch installation selector](https://pytorch.org/get-started/locally/). The implementation saves and loads a `state_dict` with PyTorch's weights-only loading mode.
