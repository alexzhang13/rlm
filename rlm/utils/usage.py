from collections.abc import Iterable

from rlm.core.types import ModelUsageSummary, UsageSummary


def merge_usage_summaries(summaries: Iterable[UsageSummary]) -> UsageSummary:
    """Sum independently executed work without mutating client-owned summaries."""
    merged: dict[str, ModelUsageSummary] = {}
    for summary in summaries:
        for model, usage in summary.model_usage_summaries.items():
            previous = merged.get(model, ModelUsageSummary(0, 0, 0))
            costs = [cost for cost in (previous.total_cost, usage.total_cost) if cost is not None]
            merged[model] = ModelUsageSummary(
                previous.total_calls + usage.total_calls,
                previous.total_input_tokens + usage.total_input_tokens,
                previous.total_output_tokens + usage.total_output_tokens,
                sum(costs) if costs else None,
            )
    return UsageSummary(merged)
