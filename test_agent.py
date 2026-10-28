import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent

def test_retrieves_delhi_el_nino():
    fs=agent.retrieve_facts("Why did Delhi become more polluted during El Nino 2023-24?")
    assert any(f["id"] in {"F3","F6","F7"} for f in fs)

def test_unsupported_question_refuses():
    r=agent.run_agent("Who won the football World Cup?", use_llm=False)
    assert r["status"] == "insufficient_evidence"
    assert "don't know" in r["answer"].lower()

def test_policy_options_have_tradeoffs_and_evidence():
    r=agent.run_agent("What policy options should government consider?", use_llm=False)
    assert r["status"] == "answered_with_limits"
    assert len(r["policy_options"]) == 3
    assert all(len(p["trade_offs"]) >= 2 for p in r["policy_options"])
    assert all(p["evidence"] for p in r["policy_options"])

def test_unknown_fact_ids_flagged():
    r=agent.tool_check_evidence(["F1", "F999"])
    assert r["unknown_ids"] == ["F999"]

def test_article_limitations_are_available():
    r=agent.tool_compare_winter_patterns()
    assert r["caveat"]["id"] == "F10"


def test_generic_india_question_refuses():
    r=agent.run_agent("What is the capital of India?", use_llm=False)
    assert r["status"] == "insufficient_evidence"
