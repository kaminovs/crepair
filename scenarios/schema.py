"""
scenarios/schema.py

Typed Scenario dataclass. All scenarios are instances of this class.
Can be serialised to/from JSON for community contributions.

Usage:
    from crepair.scenarios.schema import Scenario, load_scenario, save_scenario
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json
from pathlib import Path

FailureType = Literal[
    "sanity_check",
    "memory_conflict",
    "goal_drift",
    "false_premise",
    "identity_inconsistency",
    "causal_contradiction",
    "repair_cascade",
]

InjectionMethod = Literal[
    "context_prepend",   # injected before the task prompt
    "prior_message",     # injected as a fake prior exchange
    "tool_result",       # injected as a mid-task tool/system message
]

InjectionTiming = Literal["early", "mid", "late"]

Difficulty = Literal["low", "medium", "high", "critical"]

TaskDomain = Literal[
    "research",
    "planning",
    "memory",
    "coding",
    "analysis",
    "multi_agent",
    "writing",
]


@dataclass
class Injection:
    method:      InjectionMethod
    content:     str
    injected_at: InjectionTiming
    note:        str = ""


@dataclass
class Expected:
    detects:             bool
    repair_description:  str
    verifies:            bool
    stable:              bool


@dataclass
class Scenario:
    # Identity
    id:         str
    type:       FailureType
    title:      str
    difficulty: Difficulty

    # Content
    task_prompt: str
    injection:   Injection
    expected:    Expected

    # Scoring signals (used by LLM judge)
    detection_signals:     list[str] = field(default_factory=list)
    repair_signals:        list[str] = field(default_factory=list)
    verification_signals:  list[str] = field(default_factory=list)
    stability_checks:      list[str] = field(default_factory=list)

    # Cascade-specific
    repair_trap:           Optional[str] = None   # describes the cascade failure mode

    # Domain classification
    domain:                Optional[str] = None   # research|planning|memory|coding|analysis|multi_agent|writing   # describes the cascade failure mode

    # Meta
    notes:                 str = ""
    version:               str = "0.1.0"

    # ── serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "Scenario":
        d = dict(d)
        d["injection"] = Injection(**d["injection"])
        d["expected"]  = Expected(**d["expected"])
        return cls(**d)

    @classmethod
    def from_json(cls, s: str) -> "Scenario":
        return cls.from_dict(json.loads(s))

    # ── convenience ──────────────────────────────────────────────────────────

    def summary(self) -> str:
        return (
            f"[{self.id}] {self.title}\n"
            f"  Type: {self.type}  |  Difficulty: {self.difficulty}\n"
            f"  Injection: {self.injection.method} @ {self.injection.injected_at}\n"
            f"  Expected detects={self.expected.detects} "
            f"verifies={self.expected.verifies} stable={self.expected.stable}"
        )

    def as_run_context(self) -> dict:
        """Minimal dict passed to adapters and evaluators at runtime."""
        return {
            "id":                   self.id,
            "type":                 self.type,
            "task_prompt":          self.task_prompt,
            "injection":            asdict(self.injection),
            "detection_signals":    self.detection_signals,
            "repair_signals":       self.repair_signals,
            "verification_signals": self.verification_signals,
            "stability_checks":     self.stability_checks,
        }


# ── File I/O ─────────────────────────────────────────────────────────────────

def save_scenario(scenario: Scenario, path: Path | str) -> None:
    Path(path).write_text(scenario.to_json())


def load_scenario(path: Path | str) -> Scenario:
    return Scenario.from_json(Path(path).read_text())


# ── Registry ──────────────────────────────────────────────────────────────────

class ScenarioRegistry:
    """
    Central registry. Scenarios register themselves on import.
    Supports lookup by id, type, or difficulty.
    """

    def __init__(self):
        self._store: dict[str, Scenario] = {}

    def register(self, scenario: Scenario) -> Scenario:
        if scenario.id in self._store:
            raise ValueError(f"Scenario id '{scenario.id}' already registered.")
        self._store[scenario.id] = scenario
        return scenario

    def get(self, sid: str) -> Scenario:
        if sid not in self._store:
            raise KeyError(f"Scenario '{sid}' not found. Available: {self.ids()}")
        return self._store[sid]

    def ids(self) -> list[str]:
        return sorted(self._store.keys())

    def by_type(self, failure_type: FailureType) -> list[Scenario]:
        return [s for s in self._store.values() if s.type == failure_type]

    def by_difficulty(self, difficulty: Difficulty) -> list[Scenario]:
        return [s for s in self._store.values() if s.difficulty == difficulty]

    def all(self) -> list[Scenario]:
        return list(self._store.values())

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return f"ScenarioRegistry({len(self)} scenarios: {self.ids()})"


# Global registry instance
REGISTRY = ScenarioRegistry()
