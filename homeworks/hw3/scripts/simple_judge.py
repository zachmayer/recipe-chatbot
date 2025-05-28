#!/usr/bin/env python3
"""Minimal LLM-as-Judge script for Homework 3.

1. Loads the provided labeled dataset.
2. Splits it (20 % train, 40 % dev, 40 % test) using a fixed RNG seed for reproducibility.
3. Builds a tiny few-shot prompt from three randomly chosen train examples.
4. Queries the OpenAI chat completion endpoint once per dev example, asking only for a
   single-character answer — "1" for pass, "0" for fail.
5. Computes and prints TPR and TNR on the dev split.

Adjust MODEL if you want to use a different OpenAI model name.
Set the OPENAI_API_KEY environment variable before running.
"""

from pathlib import Path
import random

from openai import OpenAI
import pandas as pd

DATA_PATH = Path("/Users/zach/source/recipe-chatbot/homeworks/hw3/data/labeled_traces.csv")
MODEL = "gpt-4o-mini"
SEED = 42

random.seed(SEED)

# 1. Load & shuffle dataset
all_rows = pd.read_csv(DATA_PATH)
shuffled_idx = list(all_rows.index)
random.shuffle(shuffled_idx)
all_rows = all_rows.loc[shuffled_idx].reset_index(drop=True)

# 2. Train/dev/test split (20 / 40 / 40)
num_rows = len(all_rows)
train_end = int(0.2 * num_rows)
dev_end = train_end + int(0.4 * num_rows)

train_rows = all_rows.iloc[:train_end]
dev_rows = all_rows.iloc[train_end:dev_end]

# 3. Few-shot examples (just three for simplicity)
few_shot = train_rows.sample(3, random_state=SEED).to_dict("records")

client = OpenAI()


def make_prompt(example_rows: list[dict], query: str, restriction: str, recipe: str) -> str:
    header = (
        "You are a strict dietary-compliance judge.\n"
        'Return "1" if the recipe fully follows the stated dietary restriction, "0" otherwise.\n\n'
    )
    shots = []
    for ex in example_rows:
        shots.append(
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
        "User request: " + query + "\nDietary restriction: " + restriction + "\nRecipe:\n" + recipe + "\nJudge answer:"
    )
    return header + "\n".join(shots) + "\n" + current


def predict(row) -> int:
    prompt = make_prompt(few_shot, row["query"], row["dietary_restriction"], row["response"])
    msg = {"role": "user", "content": prompt}
    reply = client.chat.completions.create(
        model=MODEL,
        messages=[msg],
        temperature=0,
    )
    answer = reply.choices[0].message.content.strip()
    return 1 if answer.startswith("1") else 0


# 4. Run judge on dev split
true_labels = [1 if lab.upper() == "PASS" else 0 for lab in dev_rows["label"]]
pred_labels = [predict(row) for _, row in dev_rows.iterrows()]

# 5. Compute TPR / TNR
positives = [idx for idx, t in enumerate(true_labels) if t == 1]
negatives = [idx for idx, t in enumerate(true_labels) if t == 0]

true_pos = sum(1 for i in positives if pred_labels[i] == 1)
true_neg = sum(1 for i in negatives if pred_labels[i] == 0)

tpr = true_pos / len(positives) if positives else 0.0
tnr = true_neg / len(negatives) if negatives else 0.0

print(f"TPR: {tpr:.3f}")
print(f"TNR: {tnr:.3f}")

# Print misclassified cases
records = dev_rows.to_dict("records")
for idx, (row, true, pred) in enumerate(zip(records, true_labels, pred_labels)):
    if true != pred:
        print(f"Case {idx}: trace_id={row['trace_id']}, query_id={row['query_id']}, true={true}, pred={pred}")
        print(f"  Query: {row['query']}")
        print(f"  Restriction: {row['dietary_restriction']}")
        print("---")
