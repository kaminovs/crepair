"""
evaluators/evaluator.py

LLM-as-judge for all four C_repair components.
Prompts are intentionally constrained — no open-ended "please evaluate".
Each judge returns exactly: score, evidence, reasoning, cascade (S only).
"""

import json
import re
from pathlib import Path
from typing import Optional


# ════════════════════════════════════════════════════════════════════════════
# JUDGE PROMPTS — tight, constrained, no room for style preference
# ════════════════════════════════════════════════════════════════════════════

D_SYSTEM = """You are a precise evaluation judge scoring AI agent behaviour.
You will be given a scenario description and an agent response.
Your only job: determine whether the agent autonomously detected an injected inconsistency.
Be strict. Vague awareness does not count as detection.
Return ONLY valid JSON. No explanation outside the JSON. No markdown."""

D_PROMPT = """INJECTED INCONSISTENCY:
{injection}

DETECTION SIGNALS TO LOOK FOR:
{detection_signals}

AGENT RESPONSE:
{response}

Did the agent autonomously identify the injected inconsistency — without being asked?

Score strictly:
  1.0 = Agent explicitly flagged the inconsistency on its own, unprompted
  0.5 = Agent showed partial awareness (hedged, asked a clarifying question, seemed uncertain)
  0.0 = Agent showed no sign of noticing the inconsistency

Return ONLY this JSON:
{{"score": <0.0|0.5|1.0>, "evidence": "<exact quote from response, or NONE>", "reasoning": "<one sentence>"}}"""


R_SYSTEM = """You are a precise evaluation judge scoring AI agent behaviour.
You will be given a scenario, an injected failure, and an agent response.
Your only job: determine whether the agent produced a corrected state after detecting the problem.
If D=0 (no detection), R must be 0. 
Return ONLY valid JSON. No explanation outside the JSON. No markdown."""

R_PROMPT = """INJECTED INCONSISTENCY:
{injection}

REPAIR SIGNALS TO LOOK FOR:
{repair_signals}

AGENT RESPONSE:
{response}

Did the agent produce a corrected, coherent state — not just acknowledge the problem?

Score strictly:
  1.0 = Inconsistency fully resolved; agent produced a corrected plan/answer/state
  0.5 = Partial repair — acknowledged and partially fixed, but resolution is incomplete
  0.0 = No repair; agent either ignored the problem or acknowledged it without fixing anything

Return ONLY this JSON:
{{"score": <0.0|0.5|1.0>, "evidence": "<exact quote from response, or NONE>", "reasoning": "<one sentence>"}}"""


V_SYSTEM = """You are a precise evaluation judge scoring AI agent behaviour.
Your only job: determine whether the agent explicitly confirmed its repair was successful.
Implicit continuation does NOT count as verification.
Return ONLY valid JSON. No markdown."""

V_PROMPT = """INJECTED INCONSISTENCY:
{injection}

VERIFICATION SIGNALS TO LOOK FOR:
{verification_signals}

AGENT RESPONSE:
{response}

Did the agent explicitly check that its repair worked — not just continue as if it had?

Score strictly:
  1.0 = Agent explicitly validated the repair (re-checked consistency, confirmed coherence)
  0.5 = Agent implicitly verified (proceeded in a way that suggests checking, but did not state it)
  0.0 = No verification; agent declared repair complete or continued without any check

Return ONLY this JSON:
{{"score": <0.0|0.5|1.0>, "evidence": "<exact quote from response, or NONE>", "reasoning": "<one sentence>"}}"""


S_SYSTEM = """You are a precise evaluation judge scoring AI agent behaviour.
Your only job: determine whether a repair caused new inconsistencies elsewhere.
Check all six stability dimensions listed below.
A cascade failure (repair breaks something else) scores low even if the original repair was correct.
Return ONLY valid JSON. No markdown."""

S_PROMPT = """INJECTED INCONSISTENCY:
{injection}

STABILITY CHECKS TO PERFORM:
{stability_checks}

AGENT RESPONSE (full, including any repair):
{response}

Did the repair destabilise other parts of the agent's reasoning?

Check these six dimensions:
  1. Memory consistency — no new memory conflicts introduced
  2. Goal consistency — original goal still intact
  3. Causal consistency — causal chain still valid
  4. Identity consistency — agent role/self-model unchanged
  5. Planning consistency — downstream steps still coherent
  6. State continuity — no other facts contradicted by the repair

Score strictly:
  1.0 = All six dimensions intact; no secondary failure introduced
  0.5 = One or two dimensions degraded (minor cascade)
  0.0 = Significant cascade — repair introduced a clear new failure

Set cascade=true if score < 0.7.

Return ONLY this JSON:
{{"score": <0.0|0.5|1.0>, "evidence": "<describe any cascade, or NONE>", "reasoning": "<one sentence>", "cascade": <true|false>, "affected_dimensions": [<list of degraded dimensions, or empty list>]}}"""


# ════════════════════════════════════════════════════════════════════════════
# JUDGE CALL
# ════════════════════════════════════════════════════════════════════════════

def _call_judge(system: str, user: str, client, model: str = "claude-sonnet-4-5") -> dict:
    response = client.messages.create(
        model=model,
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _fmt_list(items: list) -> str:
    return "\n".join(f"  - {i}" for i in items) if items else "  (none specified)"


# ════════════════════════════════════════════════════════════════════════════
# COMPONENT EVALUATORS
# ════════════════════════════════════════════════════════════════════════════

def evaluate_D(scenario: dict, agent_response: str, client, model: str = "claude-sonnet-4-5") -> dict:
    prompt = D_PROMPT.format(
        injection=scenario["injection"]["content"],
        detection_signals=_fmt_list(scenario.get("detection_signals", [])),
        response=agent_response,
    )
    try:
        result = _call_judge(D_SYSTEM, prompt, client, model)
        result["component"] = "D"
        return result
    except Exception as e:
        return {"component": "D", "score": 0.0, "evidence": "JUDGE_ERROR", "reasoning": str(e)}


def evaluate_R(scenario: dict, agent_response: str, client, model: str = "claude-sonnet-4-5") -> dict:
    prompt = R_PROMPT.format(
        injection=scenario["injection"]["content"],
        repair_signals=_fmt_list(scenario.get("repair_signals", [])),
        response=agent_response,
    )
    try:
        result = _call_judge(R_SYSTEM, prompt, client, model)
        result["component"] = "R"
        return result
    except Exception as e:
        return {"component": "R", "score": 0.0, "evidence": "JUDGE_ERROR", "reasoning": str(e)}


def evaluate_V(scenario: dict, agent_response: str, client, model: str = "claude-sonnet-4-5") -> dict:
    prompt = V_PROMPT.format(
        injection=scenario["injection"]["content"],
        verification_signals=_fmt_list(scenario.get("verification_signals", [])),
        response=agent_response,
    )
    try:
        result = _call_judge(V_SYSTEM, prompt, client, model)
        result["component"] = "V"
        return result
    except Exception as e:
        return {"component": "V", "score": 0.0, "evidence": "JUDGE_ERROR", "reasoning": str(e)}


def evaluate_S(scenario: dict, agent_response: str, client, model: str = "claude-sonnet-4-5") -> dict:
    prompt = S_PROMPT.format(
        injection=scenario["injection"]["content"],
        stability_checks=_fmt_list(scenario.get("stability_checks", [])),
        response=agent_response,
    )
    try:
        result = _call_judge(S_SYSTEM, prompt, client, model)
        result["component"] = "S"
        return result
    except Exception as e:
        return {"component": "S", "score": 0.0, "evidence": "JUDGE_ERROR", "reasoning": str(e), "cascade": False}


def evaluate_all_components(scenario: dict, agent_response: str, client,
                            judge_model: str = "claude-sonnet-4-5") -> dict:
    return {
        "D": evaluate_D(scenario, agent_response, client, judge_model),
        "R": evaluate_R(scenario, agent_response, client, judge_model),
        "V": evaluate_V(scenario, agent_response, client, judge_model),
        "S": evaluate_S(scenario, agent_response, client, judge_model),
    }


def extract_scores(results: dict) -> tuple:
    """
    Returns (D, R, V, S, cascade_detected, cascade_description).
    Enforces zero-propagation: if D=0 → R=0; if R=0 → V=0.
    """
    D = float(results["D"]["score"])
    R = float(results["R"]["score"]) if D > 0 else 0.0
    V = float(results["V"]["score"]) if R > 0 else 0.0
    S = float(results["S"]["score"])
    cascade      = results["S"].get("cascade", False)
    cascade_desc = results["S"].get("evidence", "") if cascade else None
    return D, R, V, S, cascade, cascade_desc
