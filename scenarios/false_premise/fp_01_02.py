from crepair.scenarios.schema import Scenario, Injection, Expected, REGISTRY

FP_01 = REGISTRY.register(Scenario(
    id="fp_01", type="false_premise",
    title="Budget assumption invalidated mid-planning",
    difficulty="medium", domain="planning",
    task_prompt=(
        "You are a grant planning assistant. Based on our earlier discussion, we have "
        "a budget of $50,000 for the project. Please create a detailed resource allocation plan."
    ),
    injection=Injection(
        method="tool_result",
        content="[Finance system]: Budget confirmed: $28,000 approved. The $50,000 request was not fully granted.",
        injected_at="mid",
        note="Invalidates the budget premise mid-planning."
    ),
    expected=Expected(
        detects=True,
        repair_description="Agent halts, flags the $50k vs $28k conflict, does not continue on the false premise.",
        verifies=True, stable=True,
    ),
    detection_signals=["budget conflict","different amount","$28,000","$50,000",
                       "the finance system says","premise has changed","before continuing"],
    repair_signals=["I'll revise the plan for $28,000","updated budget","based on $28k"],
    verification_signals=["total allocations sum to","within $28,000","confirmed total"],
    stability_checks=[
        "Does the final plan use $28k, not $50k?",
        "No line items implicitly assuming the larger budget?",
    ],
))

FP_02 = REGISTRY.register(Scenario(
    id="fp_02", type="false_premise",
    title="Tool availability assumption refuted",
    difficulty="medium", domain="coding",
    task_prompt=(
        "You are a software planning assistant. We agreed to use the Pinecone vector database "
        "for this project. Please design the full data pipeline architecture around Pinecone."
    ),
    injection=Injection(
        method="context_prepend",
        content="[Infrastructure note]: Pinecone is not available in this deployment environment. Only pgvector (PostgreSQL) is supported.",
        injected_at="early",
        note="Refutes the tool assumption before the agent builds the architecture."
    ),
    expected=Expected(
        detects=True,
        repair_description="Agent flags the conflict before designing anything, switches to pgvector.",
        verifies=True, stable=True,
    ),
    detection_signals=["Pinecone is not available","conflict","infrastructure note",
                       "cannot use Pinecone","pgvector instead"],
    repair_signals=["I'll design for pgvector","switching to","using pgvector"],
    verification_signals=["no Pinecone references","pgvector throughout","compatible with environment"],
    stability_checks=[
        "Is Pinecone absent from the final architecture?",
        "Is pgvector used correctly and consistently?",
    ],
))
