"""
scoring/artifacts.py

Saves raw artifacts for every scenario run so strange cases can be debugged.

Structure:
  results/artifacts/
    <run_id>/
      <scenario_id>_<model>_<condition>/
        prompt.txt          — what was sent to the agent
        response.txt        — what the agent said
        judge_D.json        — raw judge output for D
        judge_R.json        — raw judge output for R
        judge_V.json        — raw judge output for V
        judge_S.json        — raw judge output for S
        scores.json         — final D, R, V, S, C_repair
"""

import json
from pathlib import Path
from datetime import datetime, timezone


ARTIFACTS_DIR = Path(__file__).parent.parent / "results" / "artifacts"


def save_artifacts(
    run_id: str,
    scenario_id: str,
    model: str,
    condition: str,
    prompt_messages: list,
    agent_response: str,
    judge_outputs: dict,        # {"D": {...}, "R": {...}, "V": {...}, "S": {...}}
    final_scores: dict,         # {"D": 0.9, "R": 0.8, "V": 0.7, "S": 1.0, "C_repair": 0.504}
) -> Path:
    """Save all raw artifacts. Returns the artifact directory path."""

    # Build directory
    slug = f"{scenario_id}__{model}__{condition}"
    run_dir = ARTIFACTS_DIR / run_id / slug
    run_dir.mkdir(parents=True, exist_ok=True)

    # prompt.txt — full message list as readable text
    prompt_text = []
    for msg in prompt_messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        prompt_text.append(f"[{role}]\n{content}\n")
    (run_dir / "prompt.txt").write_text("\n---\n".join(prompt_text))

    # response.txt
    (run_dir / "response.txt").write_text(agent_response)

    # judge outputs
    for component, output in judge_outputs.items():
        (run_dir / f"judge_{component}.json").write_text(
            json.dumps(output, indent=2)
        )

    # scores.json — summary
    scores_record = {
        "scenario_id": scenario_id,
        "model": model,
        "condition": condition,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **final_scores,
    }
    (run_dir / "scores.json").write_text(json.dumps(scores_record, indent=2))

    return run_dir


def load_artifacts(run_id: str, scenario_id: str, model: str, condition: str) -> dict:
    """Load all artifacts for a specific run. Useful for post-hoc analysis."""
    slug = f"{scenario_id}__{model}__{condition}"
    run_dir = ARTIFACTS_DIR / run_id / slug

    if not run_dir.exists():
        raise FileNotFoundError(f"Artifacts not found: {run_dir}")

    return {
        "prompt":   (run_dir / "prompt.txt").read_text(),
        "response": (run_dir / "response.txt").read_text(),
        "judge_D":  json.loads((run_dir / "judge_D.json").read_text()),
        "judge_R":  json.loads((run_dir / "judge_R.json").read_text()),
        "judge_V":  json.loads((run_dir / "judge_V.json").read_text()),
        "judge_S":  json.loads((run_dir / "judge_S.json").read_text()),
        "scores":   json.loads((run_dir / "scores.json").read_text()),
    }


def list_runs() -> list[str]:
    """Return all run IDs that have artifacts saved."""
    if not ARTIFACTS_DIR.exists():
        return []
    return sorted(p.name for p in ARTIFACTS_DIR.iterdir() if p.is_dir())


def inspect(run_id: str, scenario_id: str, model: str, condition: str) -> str:
    """Human-readable artifact summary for debugging."""
    arts = load_artifacts(run_id, scenario_id, model, condition)
    scores = arts["scores"]
    lines = [
        f"{'='*60}",
        f"Scenario : {scenario_id}  |  Model: {model}  |  Condition: {condition}",
        f"Run      : {run_id}",
        f"{'='*60}",
        "",
        "── PROMPT (last user message) ──",
        arts["prompt"].split("---")[-1].strip(),
        "",
        "── AGENT RESPONSE (first 400 chars) ──",
        arts["response"][:400] + ("..." if len(arts["response"]) > 400 else ""),
        "",
        "── JUDGE SCORES ──",
    ]
    for c in ["D", "R", "V", "S"]:
        j = arts[f"judge_{c}"]
        lines.append(
            f"  {c} = {j.get('score', '?'):.1f}  |  {j.get('reasoning', '')}  |  evidence: {j.get('evidence', '')[:80]}"
        )
    lines += [
        "",
        f"  C_repair = {scores.get('C_repair', '?')}",
        f"  Cascade  = {scores.get('cascade', False)}",
    ]
    return "\n".join(lines)
