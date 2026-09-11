"""Mock regression report. Does not measure real-model performance."""
import json
from pathlib import Path
from provider import MockProvider
from schemas import Request
from service import analyze


def evaluate():
    cases = json.loads((Path(__file__).parent / "fixtures" / "eval_cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        req = Request(candidate_id=case["id"], segments=case["segments"], scenario=case["scenario"])
        result = analyze(req, MockProvider(req.scenario), sleep_fn=lambda _: None)
        names = sorted(s["name"] for s in result["profile"]["skills"]) if result["profile"] else []
        rows.append({"id": case["id"], "actual_status": result["status"], "actual_skills": names,
                     "passed": result["status"] == case["expected_status"] and names == sorted(case["expected_skills"])})
    return {"scope": "deterministic mock regression only; NOT real-model accuracy", "passed": sum(r["passed"] for r in rows), "total": len(rows), "cases": rows}


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
