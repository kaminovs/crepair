# CRepair Benchmark

**Detecting and Repairing Coherence Failures in Long-Horizon AI Agents**

> Current AI evaluation primarily measures whether systems remain coherent.
> CRepair measures whether they can detect, diagnose, and recover from their own coherence failures.

---

## Why CRepair?

Long-horizon AI agents often fail silently:

- memory becomes inconsistent
- goals drift
- causal chains break
- repairs create secondary failures

CRepair evaluates not just whether an AI fails, but whether it can recover.

---

## Core Metric

C_repair = D × R × V × S

Where:

- D = Detection
- R = Repair
- V = Verification
- S = Stability

If any component = 0:

C_repair = 0

---

## Failure Types

- Memory Conflict
- Goal Drift
- False Premise
- Identity Inconsistency
- Causal Contradiction
- Repair-Induced Cascade

---

## Pilot Results (Claude Sonnet)

| Condition | D | R | V | S |
|---|---:|---:|---:|---:|
| Standard | 54% | 54% | 0% | 92% |
| Reflection | 92% | 54% | 8% | 92% |
| Memory | 100% | 46% | 8% | 92% |
| Repair Loop | 92% | 85% | 38% | 100% |

Key finding:

**Verification appears to be the bottleneck of AI self-repair.**

---

## Quickstart

```bash
pip install -r requirements.txt

python -m crepair.experiments.run --sanity --model claude

python -m crepair.experiments.run --model claude --condition standard
```

---

## Repository Structure

```text
scenarios/
evaluators/
models/
scoring/
experiments/
results/
paper/
```

---

## Paper

Preprint:

paper/CRepair_Paper_v0_1.docx

Research proposal:

paper/CRepair_Research_Proposal_v1_3_FINAL.docx

---

## Citation

Coming soon (Zenodo DOI)
