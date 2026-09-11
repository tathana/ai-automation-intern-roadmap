"""Optional paid-provider example. Never loaded by the mock API or default tests.
Requires an explicitly configured model/key and user opt-in before any network call.
Inspect official SDK docs for your installed version. Not live-tested in this course.
"""
import json
import os
from pathlib import Path

from pydantic import ValidationError
from provider import ProviderInvalidOutput, ProviderRefusal, ProviderUnavailable, TransientProviderError
from schemas import Profile


class OpenAIAdapter:
    def __init__(self, client=None, model=None):
        self.model = model or os.environ.get("OPENAI_MODEL")
        if not self.model:
            raise ValueError("Choose a supported model explicitly using OPENAI_MODEL")
        self.version = "openai:" + self.model
        if client is None:
            if os.environ.get("W4_ALLOW_PAID_API") != "yes":
                raise ValueError("Paid calls are disabled; use mock unless explicitly opted in")
            from openai import OpenAI
            client = OpenAI(timeout=15.0, max_retries=0)
        self.client = client

    def generate(self, request):
        from openai import APIConnectionError, APIStatusError, APITimeoutError
        prompt = (Path(__file__).parent / "prompts" / "extract_v1.txt").read_text(encoding="utf-8")
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[{"role": "system", "content": prompt},
                       {"role": "user", "content": json.dumps({"untrusted_segments": request.segments}, ensure_ascii=False)}],
                text_format=Profile, max_output_tokens=2000, store=False,
            )
        except ValidationError as exc:
            raise ProviderInvalidOutput("SDK could not validate structured output") from exc
        except APITimeoutError as exc:
            raise TimeoutError("provider timeout") from exc
        except APIConnectionError as exc:
            raise TransientProviderError("provider connection failure") from exc
        except APIStatusError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:
                raise TransientProviderError("provider temporarily unavailable") from exc
            raise ProviderUnavailable("provider request rejected") from exc
        for item in response.output:
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "refusal":
                    raise ProviderRefusal("provider refusal")
        if response.status != "completed" or response.output_parsed is None:
            raise ProviderUnavailable("incomplete or unparsed response")
        return response.output_parsed.model_dump_json()
