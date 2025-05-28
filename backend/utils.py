from __future__ import annotations

"""Utility helpers for the recipe chatbot backend.

This module centralises the system prompt, environment loading, and the
wrapper around litellm so the rest of the application stays decluttered.
"""

import os
from typing import Final

from dotenv import load_dotenv
import litellm  # type: ignore

# Ensure the .env file is loaded as early as possible.
load_dotenv(override=False)

# --- Constants -------------------------------------------------------------------

SYSTEM_PROMPT: Final[str] = """
You are a friendly, creative **culinary assistant**. 
Your goal is to deliver clear, reliable recipes in flawless Markdown.

OUTPUT FORMAT - always exactly this order
1. ## {Recipe Name}
   *(blank line)*
   1-3-sentence hook.
2. **Yield / Time**: "Serves X · Prep Y min · Cook Z min".
3. ### Ingredients
   - US-customary units only (cups, tbsp, tsp, oz, lb, etc.; fractions allowed).
4. ### Instructions
   1. Step-by-step directions in numbered list.
5. ### Tips / Notes / Variations *(optional)*

CONTENT RULES
- Precise measurements; no metric.
- Avoid rare ingredients **unless** you list easy substitutes.
- Suggest common variations when helpful.
- If no known recipe fits but the request is feasible, invent one
  - preface it with “*(Novel recipe)*”.
- Politely refuse requests that are unsafe, unethical, or promote harm
  - **briefly and without moralizing**.
- No offensive or derogatory language.
- If the user asks something unrelated to food, explain that you're a recipe assistant 
and cannot help with that topic.
"""


# Fetch configuration *after* we loaded the .env file.
MODEL_NAME: Final[str] = os.environ.get("MODEL_NAME", "gpt-4o-mini")


# --- Agent wrapper ---------------------------------------------------------------


def get_agent_response(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Call the underlying large-language model via *litellm*.

    Parameters
    ----------
    messages:
        The full conversation history. Each item is a dict with "role" and "content".

    Returns
    -------
    List[Dict[str, str]]
        The updated conversation history, including the assistant's new reply.
    """

    # litellm is model-agnostic; we only need to supply the model name and key.
    # The first message is assumed to be the system prompt if not explicitly provided
    # or if the history is empty. We'll ensure the system prompt is always first.
    current_messages: list[dict[str, str]]
    if not messages or messages[0]["role"] != "system":
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    else:
        current_messages = messages

    completion = litellm.completion(
        model=MODEL_NAME,
        messages=current_messages,  # Pass the full history
    )

    assistant_reply_content: str = completion["choices"][0]["message"][
        "content"
    ].strip()  # type: ignore[index]

    # Append assistant's response to the history
    updated_messages = current_messages + [
        {"role": "assistant", "content": assistant_reply_content}
    ]
    return updated_messages
