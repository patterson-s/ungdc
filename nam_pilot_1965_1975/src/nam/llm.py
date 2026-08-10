"""Thin Cohere ClientV2 wrapper. Every call logs (model, prompt_version) so it can be
stamped onto the resulting annotation/decision for provenance, per nam_discourse_plan.md S4.

Uses response_format={"type": "json_object", "json_schema": ...} for structured output
(confirmed against Cohere docs: https://docs.cohere.com/v1/docs/structured-outputs,
https://docs.cohere.com/docs/parameter-types-in-json). Not combinable with tools/documents.
"""
import json
import os

import cohere

_client = None


def get_client() -> cohere.ClientV2:
    global _client
    if _client is None:
        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            raise RuntimeError("COHERE_API_KEY is not set")
        _client = cohere.ClientV2(api_key=api_key)
    return _client


def call_json(
    *,
    model: str,
    system: str,
    user: str,
    json_schema: dict,
    prompt_version: str,
    temperature: float = 0.0,
) -> dict:
    """Call Cohere chat() with a JSON schema constraint. Returns (parsed_json, meta) where
    meta carries model/prompt_version for provenance logging by the caller."""
    co = get_client()
    response = co.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        response_format={"type": "json_object", "json_schema": json_schema},
    )
    text = response.message.content[0].text
    parsed = json.loads(text)
    meta = {"model": model, "prompt_version": prompt_version}
    return parsed, meta
