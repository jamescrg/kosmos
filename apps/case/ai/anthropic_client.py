"""
Anthropic Claude API client for AI chat.

Uses streaming to support cancellation mid-request.
"""

from typing import Callable

import anthropic
from django.conf import settings


def send_to_claude(
    system_context: str,
    messages: list[dict],
    model: str = "claude-sonnet-4-20250514",
    is_cancelled: Callable[[], bool] | None = None,
) -> tuple[str, int, int]:
    """
    Send a conversation to Claude and get a response using streaming.

    Uses streaming mode to allow cancellation mid-request. When cancelled,
    only tokens generated up to that point are billed.

    Args:
        system_context: The system prompt with matter context
        messages: List of {"role": "user"|"assistant", "content": str}
        model: Claude model to use (claude-sonnet-4-20250514 or claude-opus-4-5-20251101)
        is_cancelled: Optional callback that returns True if request should be cancelled

    Returns:
        tuple of (response_text, input_tokens, output_tokens)

    Raises:
        anthropic.APIError: If the API call fails
        InterruptedError: If the request was cancelled
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Format messages for Anthropic API
    formatted_messages = [
        {"role": msg["role"], "content": msg["content"]} for msg in messages
    ]

    # Use streaming to allow cancellation
    response_parts = []
    input_tokens = 0
    output_tokens = 0

    with client.messages.stream(
        model=model,
        max_tokens=4096,
        system=system_context,
        messages=formatted_messages,
    ) as stream:
        for text in stream.text_stream:
            # Check for cancellation on each chunk
            if is_cancelled and is_cancelled():
                raise InterruptedError("Request cancelled")
            response_parts.append(text)

        # Get final usage stats
        final_message = stream.get_final_message()
        input_tokens = final_message.usage.input_tokens
        output_tokens = final_message.usage.output_tokens

    response_text = "".join(response_parts)
    return response_text, input_tokens, output_tokens
