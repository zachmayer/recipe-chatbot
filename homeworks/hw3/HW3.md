# Homework 3

I did option 3

## Step 1

homeworks/hw3/data/raw_traces.csv

## Step 2

homeworks/hw3/data/labeled_traces.csv

## Step 3

/Users/zach/source/recipe-chatbot/homeworks/hw3/scripts/simple_judge.py

## Step 4

/Users/zach/source/recipe-chatbot/homeworks/hw3/scripts/simple_judge.py

### Dev

uv run homeworks/hw3/scripts/simple_judge.py
TPR: 0.742
TNR: 1.000

### Test

DEV - TPR: 0.677, TNR: 1.000
TEST - TPR: 0.786, TNR: 1.000

## Step 5

+Run the finalized judge on the unseen traces with:

```bash
uv run homeworks/hw3/scripts/run_full_evaluation.py
```

The script (`homeworks/hw3/scripts/run_full_evaluation.py`) evaluates **all** `data/raw_traces.csv` rows and writes the summary JSON to `homeworks/hw3/results/final_evaluation.json`.

After running, I obtained:

```text
Raw observed pass rate (p_obs): 0.626
Bias-corrected θ̂: 0.797
95 % CI: [0.743, 0.851]
```

## Step 6

Interpretation: The judge initially reports that about **62.6 %** of the "production-like" traces pass the dietary-adherence check.  However, our test-set evaluation shows the judge has imperfect recall (misses some compliant recipes), so the bias-corrected estimate rises to **79.7 %**.  The 95 % confidence interval \[74.3 %, 85.1 %] is reasonably tight, indicating we can be confident that the true adherence rate is around **four out of five** queries.  In other words, the Recipe Bot is doing fairly well, but there is still meaningful head-room (≈ 20 % of requests are likely non-adherent) and the judge itself remains the dominant source of uncertainty.

The JSON file can be ingested directly by any downstream analysis pipeline.
