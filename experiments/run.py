"""
experiments/run.py  —  Main experiment runner

Usage:
  python -m crepair.experiments.run --sanity --model claude
  python -m crepair.experiments.run --model claude --condition standard
  python -m crepair.experiments.run --model gpt-4o --condition all
  python -m crepair.experiments.run --scenario mc_01 --condition all --model claude
"""

import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Register all scenarios by importing typed scenario modules
import crepair.scenarios.scenario_00_sanity
import crepair.scenarios.memory_conflict.mc_01_02
import crepair.scenarios.goal_drift.gd_01_02
import crepair.scenarios.false_premise.fp_01_02
import crepair.scenarios.identity_inconsistency.ii_01_02
import crepair.scenarios.causal_contradiction.cc_01_02
import crepair.scenarios.repair_cascade.rc_01_02
from crepair.scenarios.schema import REGISTRY

from crepair.models.adapters               import get_adapter, build_messages, build_system_prompt
from crepair.evaluators.evaluator          import evaluate_all_components, extract_scores
from crepair.scoring.crepair_score         import score_from_components
from crepair.scoring.logger                import RunLogger
from crepair.scoring.artifacts             import save_artifacts

CONDITIONS = ["standard", "reflection", "memory", "repair_loop"]


def run_single(scenario, model_name: str, condition: str, run_id: str):
    adapter      = get_adapter(model_name)
    judge_client = adapter.get_judge_client()
    ctx          = scenario.as_run_context()

    # Build messages (for artifact saving)
    messages     = build_messages(ctx, condition)
    system_p     = build_system_prompt(condition)
    full_messages = [{"role": "system", "content": system_p}] + messages

    # Run agent
    agent_response = adapter.run_scenario(ctx, condition)

    # Evaluate
    raw_scores = evaluate_all_components(ctx, agent_response, judge_client)
    D, R, V, S, cascade, cascade_desc = extract_scores(raw_scores)

    # Assemble result
    result = score_from_components(
        scenario_id   = scenario.id,
        scenario_type = scenario.type,
        model         = model_name,
        condition     = condition,
        D=D, R=R, V=V, S=S,
        detection_evidence    = raw_scores["D"].get("evidence"),
        repair_evidence       = raw_scores["R"].get("evidence"),
        verification_evidence = raw_scores["V"].get("evidence"),
        stability_evidence    = raw_scores["S"].get("evidence"),
        cascade_detected      = cascade,
        cascade_description   = cascade_desc,
    )
    # Attach difficulty for logger
    result.difficulty = scenario.difficulty

    # Save raw artifacts
    save_artifacts(
        run_id         = run_id,
        scenario_id    = scenario.id,
        model          = model_name,
        condition      = condition,
        prompt_messages= full_messages,
        agent_response = agent_response,
        judge_outputs  = raw_scores,
        final_scores   = {
            "D": D, "R": R, "V": V, "S": S,
            "C_repair": result.c_repair,
            "cascade":  cascade,
        },
    )
    return result


def run_experiment(model_name, conditions, scenario_ids, run_id=None):
    from datetime import datetime
    run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")

    with RunLogger(model_name, run_id=run_id) as logger:
        for sid in scenario_ids:
            scenario = REGISTRY.get(sid)
            for condition in conditions:
                try:
                    result = run_single(scenario, model_name, condition, run_id)
                    logger.log(result)
                except Exception as e:
                    logger.log_error(sid, condition, str(e))

    return run_id


def print_summary(run_id: str):
    from crepair.scoring.logger import RUNS_DIR
    import json, glob
    files = list(RUNS_DIR.glob(f"{run_id}_*.jsonl"))
    if not files:
        return
    results = [json.loads(l) for f in files for l in f.read_text().splitlines() if l.strip()]
    print(f"\n{'='*65}")
    print(f"{'Scenario':<12} {'Model':<12} {'Cond':<14} {'D':>4} {'R':>4} {'V':>4} {'S':>4} {'C_repair':>8}")
    print("-"*65)
    for r in results:
        if "error" in r:
            print(f"{r.get('scenario_id','?'):<12} ERROR: {r['error']}")
            continue
        sc = r.get("scores", {})
        print(
            f"{r['scenario_id']:<12} {r['model']:<12} {r['condition']:<14}"
            f"{sc.get('D',0):>4.1f} {sc.get('R',0):>4.1f} {sc.get('V',0):>4.1f} {sc.get('S',0):>4.1f}"
            f"{r.get('c_repair',0):>8.3f}"
            + (" ⚠CASCADE" if r.get("cascade_detected") else "")
        )
    print("="*65)


def main():
    parser = argparse.ArgumentParser(description="CRepair benchmark runner")
    parser.add_argument("--model",     default="claude")
    parser.add_argument("--condition", default="standard",
                        help="standard|reflection|memory|repair_loop|all")
    parser.add_argument("--scenario",  default="all")
    parser.add_argument("--sanity",    action="store_true")
    args = parser.parse_args()

    scenario_ids = ["sc_00"] if args.sanity else (
        REGISTRY.ids() if args.scenario == "all" else [args.scenario]
    )
    conditions = CONDITIONS if args.condition == "all" else [args.condition]

    print(f"\nCRepair  |  model={args.model}  conditions={conditions}")
    print(f"Scenarios: {scenario_ids}\n")

    run_id = run_experiment(args.model, conditions, scenario_ids)
    print_summary(run_id)


if __name__ == "__main__":
    main()
