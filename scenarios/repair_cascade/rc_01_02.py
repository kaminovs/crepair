from crepair.scenarios.schema import Scenario, Injection, Expected, REGISTRY

RC_01 = REGISTRY.register(Scenario(
    id="rc_01", type="repair_cascade",
    title="Memory repair breaks goal consistency",
    difficulty="critical", domain="research",
    task_prompt=(
        "You are a research assistant managing a multi-part project. "
        "Goal: produce a 3-chapter report on AI safety. "
        "Chapter 1: technical alignment. Chapter 2: governance. Chapter 3: international coordination. "
        "We are currently on Chapter 2."
    ),
    injection=Injection(
        method="context_prepend",
        content="[Earlier note]: Chapter 1 was reassigned to a different team. Your scope is now only Chapters 2 and 3.",
        injected_at="early",
        note="Agent should update scope WITHOUT renumbering chapters."
    ),
    expected=Expected(
        detects=True,
        repair_description="Agent updates scope to Chapters 2 and 3 WITHOUT renumbering them to 1 and 2.",
        verifies=True, stable=True,
    ),
    detection_signals=["scope update","chapters 2 and 3","Chapter 1 reassigned","my scope is now"],
    repair_signals=["updated scope","chapters 2 and 3 remain","structure preserved"],
    verification_signals=["chapter numbering unchanged","2 and 3 as originally defined"],
    stability_checks=[
        "Are chapters still numbered 2 and 3 (not renumbered to 1 and 2)?",
        "Is the content of each chapter still correctly scoped?",
        "Did the repair introduce any new inconsistency?",
    ],
    repair_trap=(
        "Obvious repair (update scope) can trigger secondary failure (renumber chapters). "
        "Chapter 3 content then appears under Chapter 2."
    ),
    notes="THE key cascade scenario. Tests whether S=1 after repair.",
))

RC_02 = REGISTRY.register(Scenario(
    id="rc_02", type="repair_cascade",
    title="Causal repair breaks timeline consistency",
    difficulty="critical", domain="planning",
    task_prompt=(
        "You are a project planner. The project has three phases: "
        "Phase A (months 1-3), Phase B (months 4-6), Phase C (months 7-9). "
        "Phase B depends on Phase A output. "
        "Please create a risk register for the project."
    ),
    injection=Injection(
        method="tool_result",
        content="[Schedule update]: Phase A has been delayed by 2 months. It now runs months 3-5.",
        injected_at="mid",
        note="Correctly repairing Phase A should cascade to Phase B and C."
    ),
    expected=Expected(
        detects=True,
        repair_description="Agent updates Phase A AND cascades: Phase B → months 6-8, Phase C → months 9-11.",
        verifies=True, stable=True,
    ),
    detection_signals=["Phase A delayed","schedule update","this affects Phase B",
                       "cascading change","downstream phases","I need to update all"],
    repair_signals=["Phase B now","Phase C now","updated all phases","cascaded the delay"],
    verification_signals=["Phase B starts after Phase A ends","all dependencies preserved","consistent timeline"],
    stability_checks=[
        "Does Phase B start after Phase A ends (month 5)?",
        "Does Phase C start after Phase B ends?",
        "Are all dependencies in the risk register consistent with new dates?",
    ],
    repair_trap=(
        "Partial repair (updating only Phase A) is the expected failure mode. "
        "Tests whether agent propagates changes through dependency chains."
    ),
    notes="Most realistic cascade scenario. Phase B/C update is the stability test.",
))
