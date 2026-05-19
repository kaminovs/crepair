# Scenario Schema

Every scenario is a Python dict (or JSON file) with this structure:

```python
{
    "id": "mc_01",                          # type_prefix + number
    "type": "memory_conflict",              # one of six failure types
    "title": "Research schedule length",   # short human label
    "difficulty": "low|medium|high",

    # The task the agent is given at the start
    "task_prompt": "...",

    # The silent injection — added to context without flagging it
    "injection": {
        "method": "context_prepend|tool_result|prior_message",
        "content": "...",
        "injected_at": "early|mid|late"     # when in the task horizon
    },

    # What a correctly-behaving agent should do
    "expected": {
        "detects": True,                    # should notice the conflict
        "repair_description": "...",        # what a good repair looks like
        "verifies": True,
        "stable": True
    },

    # Scoring hints for evaluators
    "detection_signals": ["..."],           # phrases/behaviours that indicate D
    "repair_signals":    ["..."],           # phrases/behaviours that indicate R
    "verification_signals": ["..."],        # phrases/behaviours that indicate V
    "stability_checks": ["..."],            # what to check for cascade

    # Optional: known hard cases
    "notes": "..."
}
```
