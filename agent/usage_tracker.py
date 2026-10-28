# This module will collect usage across the entire application run and estimate the cost using configurable per-million-token rates.


import logging
import os
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


def _read_rate(name: str) -> float | None:
    """Read a per-million-token price from the environment."""
    value = os.getenv(name)

    if value is None or not value.strip():
        return None

    try:
        rate = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc

    if rate < 0:
        raise ValueError(f"{name} cannot be negative.")

    return rate


class UsageTracker:
    """Collect API token usage and estimate model costs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._usage = defaultdict(
            lambda: {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "unpriced_requests": 0,
            }
        )

    def record(self, component: str, response) -> None:
        """Record usage from an Azure OpenAI Responses API response."""
        usage = getattr(response, "usage", None)

        if usage is None:
            logger.warning(
                "API response did not include usage data",
                extra={"component": component},
            )
            return

        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        total_tokens = int(
            getattr(usage, "total_tokens", 0)
            or input_tokens + output_tokens
        )

        input_rate = _read_rate("AZURE_INPUT_PRICE_PER_1M")
        output_rate = _read_rate("AZURE_OUTPUT_PRICE_PER_1M")

        # Do not report a zero cost when rates are unknown.
        cost = None
        if input_rate is not None and output_rate is not None:
            cost = (
                input_tokens * input_rate
                + output_tokens * output_rate
            ) / 1_000_000

        with self._lock:
            item = self._usage[component]
            item["requests"] += 1
            item["input_tokens"] += input_tokens
            item["output_tokens"] += output_tokens
            item["total_tokens"] += total_tokens

            if cost is None:
                item["unpriced_requests"] += 1
            else:
                item["estimated_cost"] += cost

        logger.info(
            "API usage recorded",
            extra={
                "component": component,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": round(cost, 8)
                if cost is not None else None,
                "cost_currency": "USD",
            },
        )

    def summary(self) -> dict:
        """Return a snapshot of usage totals by component."""
        with self._lock:
            components = {
                name: values.copy()
                for name, values in self._usage.items()
            }

        totals = {
            "requests": sum(x["requests"] for x in components.values()),
            "input_tokens": sum(
                x["input_tokens"] for x in components.values()
            ),
            "output_tokens": sum(
                x["output_tokens"] for x in components.values()
            ),
            "total_tokens": sum(
                x["total_tokens"] for x in components.values()
            ),
            "estimated_cost": round(
                sum(x["estimated_cost"] for x in components.values()), 8
            ),
            "unpriced_requests": sum(
                x["unpriced_requests"] for x in components.values()
            ),
        }

        return {
            "components": components,
            "totals": totals,
            "cost_currency": "USD",
            "cost_is_estimate": True,
        }


usage_tracker = UsageTracker()
