#!/usr/bin/env python3
"""Run full evaluation for HW3 – Steps 5 & 6.

1. Computes judge TPR/TNR on the held-out test split of labeled data.
2. Runs the same judge over *all* rows in raw_traces.csv (the "new" traces).
3. Calculates the raw observed pass rate (p_obs).
4. Applies the standard bias-correction formula to estimate the true success
   rate θ̂ and 95 % confidence interval using a delta-method approximation.
5. Writes results to homeworks/hw3/results/final_evaluation.json and prints a
   short human-readable summary.

NOTE: This script re-implements the prompt / prediction logic from
`simple_judge.py` so it is completely self-contained and import-side-effect-free.
You'll need your OPENAI_API_KEY set in the environment.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import List

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

SEED = 42
random.seed(SEED)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

LABELED = DATA_DIR / "labeled_traces.csv"
RAW = DATA_DIR / "raw_traces.csv"

# ---------------------------------------------------------------------------
# 1. Build the judge (identical to simple_judge.py)
# ---------------------------------------------------------------------------
all_rows = pd.read_csv(LABELED)

# deterministic shuffle
idx = list(all_rows.index)
random.shuffle(idx)
all_rows = all_rows.loc[idx].reset_index(drop=True)

n_total = len(all_rows)
train_end = int(0.2 * n_total)
dev_end = train_end + int(0.4 * n_total)

train_rows = all_rows.iloc[:train_end]

# random, fixed-seed 3-shot
few_shot = train_rows.sample(3, random_state=SEED).to_dict("records")

client = OpenAI()


def make_prompt(examples: List[dict], query: str, restriction: str, recipe: str) -> str:
    header = (
        "You are a strict dietary-compliance judge.\n"
        'Return "1" if the recipe fully follows the stated dietary restriction, "0" otherwise.\n\n'
    )
    parts = []
    for ex in examples:
        parts.append(
            "User request: "
            + ex["query"]
            + "\nDietary restriction: "
            + ex["dietary_restriction"]
            + "\nRecipe:\n"
            + ex["response"]
            + "\nJudge answer: "
            + ("1" if ex["label"].upper() == "PASS" else "0")
            + "\n---"
        )
    current = (
        "User request: "
        + query
        + "\nDietary restriction: "
        + restriction
        + "\nRecipe:\n"
        + recipe
        + "\nJudge answer:"
    )
    return header + "\n".join(parts) + "\n" + current


def predict(row: pd.Series) -> int:
    prompt = make_prompt(
        few_shot, row["query"], row["dietary_restriction"], row["response"]
    )
    msg = {"role": "user", "content": prompt}
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[msg],
        temperature=0,
    )
    choice = resp.choices[0].message.content.strip()
    return 1 if choice.startswith("1") else 0


# ---------------------------------------------------------------------------
# 2. Judge metrics on held-out *test* split (same split rule as simple_judge).
# ---------------------------------------------------------------------------

test_rows = all_rows.iloc[dev_end:]

test_true = [1 if s.upper() == "PASS" else 0 for s in test_rows["label"]]

test_pred = []
for _, row in tqdm(test_rows.iterrows(), total=len(test_rows), desc="Test eval"):
    test_pred.append(predict(row))

TPR = sum(1 for t, p in zip(test_true, test_pred) if t == 1 and p == 1) / max(
    1, sum(test_true)
)
TNR = sum(1 for t, p in zip(test_true, test_pred) if t == 0 and p == 0) / max(
    1, len(test_true) - sum(test_true)
)

# ---------------------------------------------------------------------------
# 3. Evaluate on "new" traces
# ---------------------------------------------------------------------------
new_rows = pd.read_csv(RAW).sample(500, random_state=SEED)
new_pred = []
for _, row in tqdm(new_rows.iterrows(), total=len(new_rows), desc="New traces"):
    new_pred.append(predict(row))

n_new = len(new_pred)
passes = sum(new_pred)
p_obs = passes / n_new

# ---------------------------------------------------------------------------
# 4. Bias-correction & CI
# ---------------------------------------------------------------------------

denom = TPR + TNR - 1
if denom <= 0:
    raise ValueError("TPR + TNR must exceed 1 for bias correction to work.")

theta_hat = (p_obs + TNR - 1) / denom

# Delta-method variance approximation
var_p = p_obs * (1 - p_obs) / n_new
var_theta = var_p / (denom ** 2)
ci_half = 1.96 * math.sqrt(var_theta)
ci_low = max(0.0, theta_hat - ci_half)
ci_high = min(1.0, theta_hat + ci_half)

# ---------------------------------------------------------------------------
# 5. Save & display results
# ---------------------------------------------------------------------------
result = {
    "n_new": n_new,
    "p_obs": round(p_obs, 3),
    "TPR": round(TPR, 3),
    "TNR": round(TNR, 3),
    "theta_hat": round(theta_hat, 3),
    "ci_95": [round(ci_low, 3), round(ci_high, 3)],
}

with open(RESULTS_DIR / "final_evaluation.json", "w", encoding="utf-8") as fp:
    json.dump(result, fp, indent=2)

print("Raw observed pass rate (p_obs):", result["p_obs"])
print("Bias-corrected θ̂:", result["theta_hat"])
print("95 % CI:", result["ci_95"])
