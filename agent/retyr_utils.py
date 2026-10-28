# This module will centralize retry behavior so you can reuse it in both your planner and researcher.
# Agent calls Azure OpenAI multiple times, and a temporary timeout or rate limit can occur
# tenactity has  Stopping Criteria,  3. Waiting Strategies (Backoff),  4. Filtering Specific Exceptions or Results







from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential
)


def is_retryable_azure_error(exc: Exception) -> bool:
    """Return True only for errors that may succeed on a later attempt."""

    if isinstance(
        exc,
        (
            APIConnectionError,
            APITimeoutError,
            RateLimitError,
            InternalServerError,
        ),
    ):
        return True

    if isinstance(exc, APIStatusError):
        return (
            exc.status_code in {408, 409, 429}
            or exc.status_code >= 500
        )

    return False


def retry_azure_call(function, *args, **kwargs):
    """Retry a transient Azure OpenAI request at most three times."""

    @retry(
        retry=retry_if_exception(is_retryable_azure_error),
        stop=stop_after_attempt(3),
        wait=wait_random_exponential(
            multiplier=1,
            min=1,
            max=10,
        ),
        reraise=True,
    )
    def execute():
        return function(*args, **kwargs)

    return execute()
