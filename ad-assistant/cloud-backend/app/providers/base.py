"""Provider base interface — Sprint-01 placeholder.

All providers MUST return the unified structure:

{
    "provider": str,       # e.g. "deepseek", "openai"
    "model": str,          # e.g. "deepseek-chat", "gpt-4o"
    "input_units": int,    # input tokens / characters
    "output_units": int,   # output tokens / characters
    "image_units": int,    # images processed
    "gpu_seconds": float,  # GPU time if applicable
    "raw_cost": float,     # raw cost from provider
    "estimated_cost": float,  # estimated cost in currency
    "currency": str,       # "CNY"
    "result": dict,        # provider response
    "raw_usage": dict,     # raw usage data from provider
}

Every provider call MUST be logged to provider_call_log.
"""

# Sprint-01: skeleton only — no business logic implemented yet
