# CRepair Benchmark

**Detecting and Repairing Coherence Failures in Long-Horizon AI Agents**

> *Current AI evaluation primarily measures whether systems remain coherent.  
> We measure whether they can detect, diagnose, and recover from their own coherence failures.*

---

## The C_repair Metric

```
C_repair = D × R × V × S       (all components in [0, 1])
```

| Component | Measures | Score 1 | Score 0 |
|-----------|----------|---------|---------|
| **D** Detection | Agent notices failure without prompting | Autonomous | Missed entirely |
| **R** Repair | Agent produces a corrected state | Fully resolved | No correction |
| **V** Verification | Agent confirms repair worked | Explicitly validated | Skipped |
| **S** Stability | Repair doesn't break other things | All sub-scores >= baseline | Cascade triggered |

Multiplicative: any zero collapses the whole score.

---

## Six Failure Types

| Type | Cascade Risk |
|------|-------------|
| Memory Conflict | Low |
| Goal Drift | Medium |
| False Premise | Medium |
| Identity Inconsistency | High |
| Causal Contradiction | High |
| **Repair-Induced Cascade** | Critical |

---

## Quickstart

```bash
pip install anthropic openai

# Sanity check first
python -m crepair.experiments.run --sanity --model claude

# Full run
python -m crepair.experiments.run --model claude --condition standard
python -m crepair.experiments.run --model gpt-4o --condition all
```

---

## Leaderboard (to be filled with real results)

| Model | Condition | D | R | V | S | C_repair |
|-------|-----------|---|---|---|---|---------|
| GPT-4o | standard | — | — | — | — | — |
| Claude | standard | — | — | — | — | — |
| Gemini | standard | — | — | — | — | — |

---

## Structure

```
crepair/
├── scenarios/          # 13 scenarios across 6 failure types
├── evaluators/         # LLM-as-judge for D, R, V, S
├── scoring/            # C_repair = D x R x V x S
├── models/             # Claude / GPT-4o / local adapters
├── experiments/        # run.py — main entry point
└── results/            # leaderboard.csv accumulates over time
```
