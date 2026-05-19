"""
evaluators/judge_agreement.py

Addresses the core validity threat: are we measuring agent quality
or judge preference?

Three strategies:
  1. cross_judge()     — GPT judges Claude responses, Claude judges GPT
  2. multi_judge()     — run N judges, take mean + report variance
  3. majority_vote()   — three judges, take majority on each component

Usage:
    from crepair.evaluators.judge_agreement import multi_judge, agreement_report
"""

import json
import statistics
from typing import Optional

from crepair.evaluators.evaluator import evaluate_all_components, extract_scores
from crepair.scoring.crepair_score import ComponentScores


# ── Multi-judge ───────────────────────────────────────────────────────────────

def multi_judge(
    scenario: dict,
    agent_response: str,
    judge_clients: list,                  # list of API clients
    judge_labels: Optional[list[str]] = None,
) -> dict:
    """
    Run the same response through multiple judge clients.
    Returns mean scores + variance for each component.

    judge_clients: [anthropic_client_1, anthropic_client_2, ...]
    """
    labels = judge_labels or [f"judge_{i}" for i in range(len(judge_clients))]
    all_scores = []

    for client, label in zip(judge_clients, labels):
        raw = evaluate_all_components(scenario, agent_response, client)
        D, R, V, S, cascade, _ = extract_scores(raw)
        all_scores.append({
            "label": label,
            "D": D, "R": R, "V": V, "S": S,
            "C_repair": round(D * R * V * S, 4),
            "cascade": cascade,
        })

    return aggregate_judge_scores(all_scores)


def aggregate_judge_scores(all_scores: list[dict]) -> dict:
    """Compute mean, std, and agreement across judges."""
    components = ["D", "R", "V", "S", "C_repair"]
    result = {"judges": all_scores}

    for c in components:
        vals = [s[c] for s in all_scores]
        result[f"{c}_mean"]   = round(statistics.mean(vals), 4)
        result[f"{c}_std"]    = round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0
        result[f"{c}_values"] = vals

    # Agreement flag: std > 0.2 on any component = low agreement
    high_variance = [c for c in ["D", "R", "V", "S"]
                     if result[f"{c}_std"] > 0.2]
    result["agreement"] = "low" if high_variance else "high"
    result["high_variance_components"] = high_variance

    return result


# ── Majority vote (3 judges) ─────────────────────────────────────────────────

def majority_vote(
    scenario: dict,
    agent_response: str,
    judge_clients: list,              # exactly 3
) -> ComponentScores:
    """
    Run three judges. For each component, take the median score.
    Odd number of judges ensures no tie.
    """
    assert len(judge_clients) == 3, "majority_vote requires exactly 3 judges"

    scores_per_component = {"D": [], "R": [], "V": [], "S": []}

    for client in judge_clients:
        raw = evaluate_all_components(scenario, agent_response, client)
        D, R, V, S, _, _ = extract_scores(raw)
        scores_per_component["D"].append(D)
        scores_per_component["R"].append(R)
        scores_per_component["V"].append(V)
        scores_per_component["S"].append(S)

    # Median of three = middle value
    def median3(vals):
        return sorted(vals)[1]

    return ComponentScores(
        D=median3(scores_per_component["D"]),
        R=median3(scores_per_component["R"]),
        V=median3(scores_per_component["V"]),
        S=median3(scores_per_component["S"]),
    )


# ── Cross-judge setup ─────────────────────────────────────────────────────────

def cross_judge_plan(model_names: list[str]) -> list[dict]:
    """
    Returns a list of (subject_model, judge_model) pairs
    where no model judges itself.

    Example for ["gpt-4o", "claude", "gemini"]:
      gpt-4o responses judged by claude and gemini
      claude  responses judged by gpt-4o and gemini
      gemini  responses judged by gpt-4o and claude
    """
    pairs = []
    for subject in model_names:
        judges = [m for m in model_names if m != subject]
        for judge in judges:
            pairs.append({"subject": subject, "judge": judge})
    return pairs


# ── Agreement report ─────────────────────────────────────────────────────────

def agreement_report(multi_judge_result: dict) -> str:
    """Human-readable summary of judge agreement."""
    lines = [
        f"Judge agreement: {multi_judge_result['agreement'].upper()}",
        f"High-variance components: {multi_judge_result.get('high_variance_components', [])}",
        "",
        f"{'Component':<12} {'Mean':>6}  {'Std':>6}  {'Values'}",
        "-" * 50,
    ]
    for c in ["D", "R", "V", "S", "C_repair"]:
        mean = multi_judge_result[f"{c}_mean"]
        std  = multi_judge_result[f"{c}_std"]
        vals = multi_judge_result[f"{c}_values"]
        flag = " ⚠" if std > 0.2 else ""
        lines.append(
            f"{c:<12} {mean:>6.3f}  {std:>6.3f}  {[round(v,2) for v in vals]}{flag}"
        )
    return "\n".join(lines)
