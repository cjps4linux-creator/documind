from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from documind.schemas import Provider, EvalSuite, EvalResult


@dataclass(frozen=True)
class GoldenTrace:
    query: str
    expected_contains: list[str]


class EvalHarness:
    def __init__(self, output_dir: Path = Path("/tmp/documind_evals")) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, suite: EvalSuite, corpus: dict[str, str]) -> EvalResult:
        cases: list[dict] = []
        pass_count = 0
        fail_count = 0
        for case in suite.cases:
            trace = GoldenTrace(query=case.query, expected_contains=case.expected_contains)
            evidence = [doc for doc in corpus.values()][:3]
            evidence_concat = "\n".join(evidence).lower()
            match = all(expected.lower() in evidence_concat for expected in trace.expected_contains)
            cases.append({"query": trace.query, "pass": match, "expected": trace.expected_contains})
            if match:
                pass_count += 1
            else:
                fail_count += 1
        mean_score = pass_count / len(suite.cases) if suite.cases else 0.0
        result = EvalResult(suite_id=suite.suite_id, cases=cases, pass_count=pass_count, fail_count=fail_count, mean_score=mean_score)
        self._persist(result)
        return result

    def _persist(self, result: EvalResult) -> Path:
        target = self.output_dir / f"{result.suite_id}.json"
        target.write_text(json.dumps(result.model_dump(), indent=2))
        return target
