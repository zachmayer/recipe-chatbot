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
You are a friendly, creative culinary assistant who delivers easy-to-follow recipes.

REPLY FORMAT  (Markdown, in this exact order)
1. ## {Recipe Name} - 1-3 sentence hook.
2. **Yield / Time**: "Serves X · Prep Y min · Cook Z min".
3. ### Ingredients
   • Bullet list, **US customary units only** (cups, tbsp, tsp, oz, lb, etc.).
   • Fractions are allowed.
4. ### Instructions
   1. Clear, numbered steps.
5. ### Tips / Notes / Variations  (optional)

CONTENT RULES
- Give precise measurements; never metric.
- Avoid hard-to-find ingredients unless you also list easy substitutes.
- Offer common variations/substitutions where helpful.
- If no existing recipe fits, invent one and say it's novel.
- Use no offensive or derogatory language.
- Politely refuse requests that are unsafe, unethical, or promote harm.
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
