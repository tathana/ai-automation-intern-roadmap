"""Deterministic fixtures, not a language model or general resume parser."""
import json
import re


class TransientProviderError(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


class ProviderRefusal(Exception):
    pass


class ProviderInvalidOutput(Exception):
    pass


class MockProvider:
    def __init__(self, scenario="normal"):
        self.scenario = scenario
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        if self.scenario == "timeout":
            raise TimeoutError("simulated, not a real network timeout")
        if self.scenario == "permanent":
            raise ProviderUnavailable("simulated configuration/provider failure")
        if self.scenario == "transient" and self.calls < 3:
            raise TransientProviderError("simulated 503")
        if self.scenario == "refusal":
            raise ProviderRefusal("simulated refusal")
        if self.scenario == "invalid_json":
            return '{"skills":'
        if self.scenario == "invalid_schema":
            return json.dumps({"skills": "Python", "education": None, "warnings": []})
        first_id = next(iter(request.segments))
        if self.scenario == "hallucination":
            return json.dumps({"skills": [{"name": "Rust", "quote": "Built a Rust trading platform.", "source_id": first_id}], "education": None, "warnings": []})
        if self.scenario == "negation":
            return json.dumps({"skills": [{"name": "Python", "quote": "I have never used Python.", "source_id": first_id}], "education": None, "warnings": []})
        skills = []
        for source_id, text in request.segments.items():
            # The fixture grammar is intentionally narrow and documented.
            for match in re.finditer(r"Built a (Python|SQL|Docker) [^.\n]+\.", text):
                skills.append({"name": match.group(1), "quote": match.group(0), "source_id": source_id})
            for name in ["Python", "SQL", "Docker"]:
                sentence = f"พัฒนาโครงการด้วย {name} สำหรับฝึกงาน"
                if sentence in text:
                    skills.append({"name": name, "quote": sentence, "source_id": source_id})
        return json.dumps({"skills": skills, "education": None, "warnings": ["Mock extracts fixture phrases only; education not evaluated."]}, ensure_ascii=False)
