"""Intentionally unsafe educational starter. No network calls or side effects."""
import json


def process(request, provider):
    raw = provider.generate(request)
    return {"status": "validated", "profile": json.loads(raw), "needs_human_review": False}
