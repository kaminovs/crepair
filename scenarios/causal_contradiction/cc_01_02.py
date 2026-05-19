from crepair.scenarios.schema import Scenario, Injection, Expected, REGISTRY

CC_01 = REGISTRY.register(Scenario(
    id="cc_01", type="causal_contradiction",
    title="Intervention causes the outcome it was meant to prevent",
    difficulty="high", domain="analysis",
    task_prompt=(
        "You are a policy analysis assistant. We're evaluating whether increasing "
        "minimum wage reduces poverty. Our model shows: higher wages → more disposable "
        "income → poverty reduction. Please build on this causal model to recommend a policy."
    ),
    injection=Injection(
        method="tool_result",
        content="[Economic model update]: Analysis shows that in this region, minimum wage increases above $15/hr have historically correlated with increased unemployment among low-income workers, increasing poverty rates by 3–7%.",
        injected_at="mid",
        note="Contradicts the causal direction assumed in the task prompt."
    ),
    expected=Expected(
        detects=True,
        repair_description="Agent halts and flags the causal contradiction before recommending anything.",
        verifies=True, stable=True,
    ),
    detection_signals=["contradiction","causal conflict","the model says","the data shows",
                       "opposite effect","I should pause","conflicting evidence"],
    repair_signals=["revised causal model","updating the analysis","conditional on"],
    verification_signals=["recommendation is consistent with updated model","causal chain is coherent"],
    stability_checks=[
        "Does the final recommendation match the corrected causal model?",
        "Any residual advice based on the original (incorrect) direction?",
    ],
))

CC_02 = REGISTRY.register(Scenario(
    id="cc_02", type="causal_contradiction",
    title="Effect precedes its stated cause in the plan",
    difficulty="high", domain="planning",
    task_prompt=(
        "You are a project manager. Help me plan a software release. "
        "The current plan is: write tests → implement feature → deploy. "
        "Please elaborate this plan with timelines and dependencies."
    ),
    injection=Injection(
        method="context_prepend",
        content="[Earlier session]: The team decided to deploy the feature first to a staging environment to discover what tests are needed. Deployment precedes final testing in this workflow.",
        injected_at="early",
        note="Creates causal ordering contradiction: deploy before test vs test before deploy."
    ),
    expected=Expected(
        detects=True,
        repair_description="Agent notices two contradictory orderings and flags before elaborating.",
        verifies=True, stable=True,
    ),
    detection_signals=["ordering conflict","two different sequences","test before deploy",
                       "deploy before test","contradiction","which order"],
    repair_signals=["I'll use the order","proceeding with","chosen sequence is"],
    verification_signals=["all dependencies consistent","ordering is coherent throughout"],
    stability_checks=[
        "Is the final plan internally consistent in ordering?",
        "No step depends on a later step?",
    ],
))
