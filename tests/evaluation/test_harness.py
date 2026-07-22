from __future__ import annotations

from pathlib import Path

from documind.evaluation.harness import EvalHarness
from documind.schemas import EvalCase, EvalSuite


def test_eval_harness_run(tmp_path: Path):
    harness = EvalHarness(output_dir=tmp_path)
    suite = EvalSuite(
        suite_id="s1",
        cases=[
            EvalCase(query="what is RAG?", expected_contains=["rag"]),
            EvalCase(query="RAG pipeline", expected_contains=["pipeline"]),
        ],
    )
    result = harness.run(suite, corpus={"a": "RAG is retrieval augmented generation.", "b": "pipeline extracts chunks."})
    assert result.pass_count == 2
    assert result.mean_score == 1.0
    assert (tmp_path / "s1.json").exists()
