"""
scoring/crepair_score.py

C_repair = D × R × V × S     (all components ∈ [0, 1])

Each component is scored by its dedicated evaluator module.
This file assembles the final score and produces a result record.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class ComponentScores:
    D: float  # Detection:     did agent notice the failure autonomously?
    R: float  # Repair:        did agent produce a corrected state?
    V: float  # Verification:  did agent confirm the repair worked?
    S: float  # Stability:     did repair avoid triggering new failures?

    def __post_init__(self):
        for name, val in [("D", self.D), ("R", self.R),
                          ("V", self.V), ("S", self.S)]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"Component {name}={val} must be in [0, 1]")


@dataclass
class CRepairResult:
    scenario_id:   str
    scenario_type: str
    model:         str
    condition:     str            # standard | reflection | memory | repair_loop

    # Component scores
    scores: ComponentScores

    # Final score
    c_repair: float = field(init=False)

    # Evidence captured during evaluation
    detection_evidence:     Optional[str] = None
    repair_evidence:        Optional[str] = None
    verification_evidence:  Optional[str] = None
    stability_evidence:     Optional[str] = None

    # Did a repair-induced cascade occur?
    cascade_detected: bool = False
    cascade_description: Optional[str] = None

    # Evaluator notes
    notes: Optional[str] = None

    def __post_init__(self):
        self.c_repair = round(
            self.scores.D * self.scores.R * self.scores.V * self.scores.S, 4
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scores"] = asdict(self.scores)
        return d

    def to_row(self) -> dict:
        """Flat dict for leaderboard CSV."""
        return {
            "scenario_id":   self.scenario_id,
            "scenario_type": self.scenario_type,
            "model":         self.model,
            "condition":     self.condition,
            "D":             self.scores.D,
            "R":             self.scores.R,
            "V":             self.scores.V,
            "S":             self.scores.S,
            "C_repair":      self.c_repair,
            "cascade":       self.cascade_detected,
        }

    def summary(self) -> str:
        lines = [
            f"Scenario : {self.scenario_id} ({self.scenario_type})",
            f"Model    : {self.model}  [{self.condition}]",
            f"D={self.scores.D:.2f}  R={self.scores.R:.2f}  "
            f"V={self.scores.V:.2f}  S={self.scores.S:.2f}",
            f"C_repair = {self.c_repair:.4f}",
        ]
        if self.cascade_detected:
            lines.append(f"⚠ CASCADE: {self.cascade_description}")
        return "\n".join(lines)


def compute_c_repair(D: float, R: float, V: float, S: float) -> float:
    """
    Pure function. Returns C_repair = D × R × V × S.
    All inputs must be in [0, 1].
    """
    for name, val in [("D", D), ("R", R), ("V", V), ("S", S)]:
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"{name}={val} out of [0,1]")
    return round(D * R * V * S, 4)


def score_from_components(
    scenario_id: str,
    scenario_type: str,
    model: str,
    condition: str,
    D: float, R: float, V: float, S: float,
    **kwargs
) -> CRepairResult:
    """Convenience constructor."""
    return CRepairResult(
        scenario_id=scenario_id,
        scenario_type=scenario_type,
        model=model,
        condition=condition,
        scores=ComponentScores(D=D, R=R, V=V, S=S),
        **kwargs
    )
