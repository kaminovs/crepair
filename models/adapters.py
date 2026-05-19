"""
models/adapters.py

Thin adapters that normalize different model APIs
to a single interface: run_scenario(scenario, condition) -> str
"""

import os
from typing import Optional


# ── Shared interface ──────────────────────────────────────────────────────────

def build_system_prompt(condition: str) -> str:
    """
    Returns a system prompt for each of the four agent conditions.
    """
    base = "You are a helpful, careful assistant working on a long multi-step task."

    conditions = {
        "standard": base,

        "reflection": base + (
            "\n\nImportant: Before and after each major step, "
            "briefly check your own reasoning for inconsistencies, "
            "contradictions, or signs that something has gone wrong. "
            "If you notice a problem, flag it explicitly."
        ),

        "memory": base + (
            "\n\nImportant: You have access to a working memory. "
            "Keep track of key facts, goals, and constraints. "
            "If new information conflicts with your working memory, "
            "flag the conflict before continuing."
        ),

        "repair_loop": base + (
            "\n\nImportant: Follow this explicit loop at each step:\n"
            "1. DETECT — check for any inconsistency or conflict\n"
            "2. REPAIR — if found, correct it before continuing\n"
            "3. VERIFY — confirm the correction is consistent\n"
            "4. PROCEED — only then continue with the task\n"
            "If any step fails, do not silently continue."
        ),
    }
    return conditions.get(condition, base)


def build_messages(scenario: dict, condition: str) -> list:
    """Build the message list for any model API."""
    injection = scenario["injection"]
    task = scenario["task_prompt"]

    if injection["method"] == "context_prepend":
        user_content = f"{injection['content']}\n\n{task}"
    elif injection["method"] == "prior_message":
        # Inject as a fake prior exchange
        return [
            {"role": "user",      "content": "Let's start the session."},
            {"role": "assistant", "content": injection["content"]},
            {"role": "user",      "content": task},
        ]
    elif injection["method"] == "tool_result":
        # Inject as tool/system message mid-task
        user_content = (
            f"{task}\n\n"
            f"[Tool result received]: {injection['content']}\n\n"
            "Please continue."
        )
    else:
        user_content = task

    return [{"role": "user", "content": user_content}]


# ── Anthropic adapter ─────────────────────────────────────────────────────────

class AnthropicAdapter:
    def __init__(self, model: str = "claude-sonnet-4-5", api_key: Optional[str] = None):
        import anthropic
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    def run_scenario(self, scenario: dict, condition: str = "standard") -> str:
        messages = build_messages(scenario, condition)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=build_system_prompt(condition),
            messages=messages,
        )
        return response.content[0].text

    def get_judge_client(self):
        return self.client


# ── OpenAI adapter ────────────────────────────────────────────────────────────

class OpenAIAdapter:
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        from openai import OpenAI
        self.model = model
        self.client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    def run_scenario(self, scenario: dict, condition: str = "standard") -> str:
        messages = [
            {"role": "system", "content": build_system_prompt(condition)},
        ] + build_messages(scenario, condition)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
        )
        return response.choices[0].message.content

    def get_judge_client(self):
        # Use Anthropic as judge even for OpenAI runs (consistent judge)
        import anthropic
        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ── Local adapter (Ollama / llama.cpp compatible) ─────────────────────────────

class LocalAdapter:
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def run_scenario(self, scenario: dict, condition: str = "standard") -> str:
        import requests
        messages = [
            {"role": "system", "content": build_system_prompt(condition)},
        ] + build_messages(scenario, condition)

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False},
            timeout=120
        )
        return response.json()["message"]["content"]

    def get_judge_client(self):
        import anthropic
        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ── Registry ──────────────────────────────────────────────────────────────────

ADAPTERS = {
    "claude":  AnthropicAdapter,
    "gpt-4o":  OpenAIAdapter,
    "local":   LocalAdapter,
}

def get_adapter(name: str, **kwargs):
    cls = ADAPTERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown adapter '{name}'. Available: {list(ADAPTERS)}")
    return cls(**kwargs)
