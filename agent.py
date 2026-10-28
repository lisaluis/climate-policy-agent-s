"""Article-grounded climate policy agent.

Pipeline: classify intent -> retrieve article facts -> apply evidence threshold ->
select a skill -> optionally synthesise with Groq -> validate citations -> return result.
Without GROQ_API_KEY, the agent remains usable through a conservative evidence-first mode.
"""
from __future__ import annotations
import json, os, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FACTS_PATH = ROOT / "data" / "facts.json"
POLICY_SKILLS = {
    "forecasting": "ENSO-aware seasonal pollution forecasting",
    "airshed": "Regional airshed-level action plans across state borders",
    "agriculture": "Climate-informed crop-calendar advisories",
}
STOP = {"what","why","how","when","where","which","does","did","the","and","for","from","with","that","this","are","was","were","can","could","should","would","about","article","tell","explain","please","give","me","you","your","is","it","in","on","of","to","a","an","as","be","do","if","not","based"}

class AgentRefusal(Exception): pass

def load_facts() -> list[dict[str, Any]]:
    return json.loads(FACTS_PATH.read_text(encoding="utf-8"))

def tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", text.lower()) if t not in STOP and len(t) > 1}

def classify_intent(question: str) -> str:
    q = question.lower()
    if any(x in q for x in ["recommend", "policy", "government", "what should", "options", "action plan", "advisory", "advice for farmers"]): return "policy_analysis"
    if any(x in q for x in ["compare", "difference", "2022", "2023", "2024", "la nina", "el nino"]): return "comparison"
    if any(x in q for x in ["sowing", "harvesting", "crop", "farmer", "agriculture", "semi-arid", "climate zone"]): return "agriculture_climate"
    if any(x in q for x in ["source", "evidence", "limitations", "reliable", "causality", "causal", "study", "research"]): return "evidence_review"
    return "article_qa"

def retrieve_facts(question: str, facts: list[dict] | None = None, limit: int = 6) -> list[dict]:
    facts = facts or load_facts(); q_tokens = tokenize(question)
    if not q_tokens: return []
    ranked=[]
    for f in facts:
        ft = tokenize(f["fact"] + " " + f["topic"] + " " + " ".join(f.get("tags", [])))
        overlap = len(q_tokens & ft)
        # Query-specific aliases help short questions such as "ENSO?".
        q=question.lower(); extra=0
        for term, bonus in [("enso", ["la nina","el nino","weather"]),("pollution",["pm2.5","air quality"]),("climate change",["climate zone"]),("farm",["agriculture","crop calendar"]),("emissions",["local emissions"]),("wind",["winds","meteorology"])]:
            if term in q and any(x in (f["fact"]+" "+" ".join(f.get("tags",[]))).lower() for x in bonus): extra += 1
        score=overlap+extra
        if score: ranked.append((score, f))
    ranked.sort(key=lambda x:(x[0], x[1]["id"]), reverse=True)
    return [f for _,f in ranked[:limit]]

def _is_article_related(question: str, retrieved: list[dict]) -> bool:
    q=question.lower()
    anchors=["enso","el nino","el niño","la nina","la niña","pm2.5","pollution","air quality","climate","weather","wind","emission","agriculture","crop","farmer","sowing","harvest","jaipur","delhi","mumbai","hyderabad","uttar pradesh","policy","study","article","rainfall","semi-arid","semi arid","2022","2023","2024","la nina","el nino"]
    return bool(retrieved) and any(a in q for a in anchors)

def _fallback(question: str, intent: str, facts: list[dict]) -> dict:
    if not facts or not _is_article_related(question, facts):
        return {"status":"insufficient_evidence", "intent":intent, "answer":"I don't know from the assigned article. The article-grounded evidence available to this agent does not support a reliable answer to that question. Try asking about the two winters, PM2.5, ENSO, winds, climate-zone shifts or farming implications.", "evidence":[], "limitations":["No relevant article evidence was retrieved."], "next_step":"Narrow the question to a topic covered by the assigned article."}
    lead = "The article reports the following relevant evidence:"
    bullets=[f"{f['id']}: {f['fact']}" for f in facts[:4]]
    limitations=[]
    if any(f["id"]=="F10" for f in facts) or intent=="evidence_review": limitations.append("The PM2.5 comparison covers only two unusual winters; the article cautions that correlations do not prove causation or guarantee the same pattern in other years.")
    if intent=="policy_analysis":
        all_facts = load_facts()
        by_id = {f["id"]: f for f in all_facts}
        return {"status":"answered_with_limits", "intent":intent, "answer":"Based on the article, consider these policy options as proposals—not as policies tested by the studies.", "evidence":[f["id"] for f in facts], "policy_options":[
          {"option":POLICY_SKILLS["forecasting"],"why":"Use seasonal ENSO and meteorological outlooks as one input to winter preparedness, alongside emissions data.","trade_offs":["Forecast uncertainty can produce false alarms.","Monitoring and forecast capacity require sustained funding."],"evidence":[by_id[x]["id"] for x in ["F4","F7","F10"]]},
          {"option":POLICY_SKILLS["airshed"],"why":"Coordinate pollution monitoring and response across connected regions because air masses can carry pollutants across city and state boundaries.","trade_offs":["Coordination across jurisdictions can be slow.","Shared data standards and responsibilities need agreement."],"evidence":[by_id[x]["id"] for x in ["F5","F8","F9"]]},
          {"option":POLICY_SKILLS["agriculture"],"why":"Pair long-term climate-zone information with local agronomic advice and updated seasonal observations before changing crop calendars.","trade_offs":["Advice must be locally validated and accessible to smallholders.","A climate-zone trend alone cannot determine a specific farm's sowing date."],"evidence":[by_id[x]["id"] for x in ["F11","F12","F13","F14"]]},
        ],"limitations":["These are policy proposals inferred from the article, not recommendations evaluated by the cited studies.","The PM2.5 study covers two winters and does not establish direct causality."]}
    answer=lead+"\n\n"+"\n".join("• "+b for b in bullets)
    return {"status":"answered_with_limits", "intent":intent, "answer":answer, "evidence":[f["id"] for f in facts[:4]], "limitations":limitations or ["This response is limited to the supplied article facts; it is not a live air-quality reading or forecast."], "next_step":"Ask a narrower follow-up if you need a specific city, winter or policy implication."}

def validate_citations(result: dict, allowed_ids: set[str]) -> dict:
    cited=set(re.findall(r"F\d+", json.dumps(result, ensure_ascii=False)))
    unknown=cited-allowed_ids
    if unknown: raise ValueError(f"Agent returned unknown fact ids: {sorted(unknown)}")
    evidence=result.get("evidence", [])
    if result.get("status") != "insufficient_evidence" and not evidence:
        raise ValueError("Answered result must include at least one evidence ID")
    if not set(evidence).issubset(allowed_ids): raise ValueError("Evidence list contains an unknown fact ID")
    return result

def run_agent(question: str, use_llm: bool | None = None) -> dict:
    question=(question or "").strip()
    if not question: return {"status":"needs_question","answer":"Please enter a question about the assigned climate and air-pollution article."}
    if len(question)>700: return {"status":"needs_shorter_question","answer":"Please shorten your question to 700 characters or fewer."}
    facts=load_facts(); retrieved=retrieve_facts(question, facts)
    intent=classify_intent(question)
    if not retrieved or not _is_article_related(question, retrieved):
        return _fallback(question,intent,[])
    want_llm = bool(os.environ.get("GROQ_API_KEY")) if use_llm is None else use_llm
    if want_llm and os.environ.get("GROQ_API_KEY"):
        try:
            from groq import Groq
            model=os.environ.get("GROQ_MODEL","openai/gpt-oss-120b")
            fact_context="\n".join(f"{f['id']}: {f['fact']} [Source: {f['source']}]" for f in retrieved)
            system=("You are a careful article-grounded research and policy agent, not a casual chatbot. "
            "Use only supplied facts. If the facts do not answer the question, return status insufficient_evidence and explicitly say you do not know from the article. "
            "Never invent numbers, citations, causal claims or sources. Separate article findings from your own policy proposals. Cite only provided fact IDs. "
            "Return JSON with status, intent, answer, evidence (list of IDs), limitations (list), next_step; for policy_analysis also policy_options, each with option, why, trade_offs (at least two), evidence (IDs).")
            user=f"Question: {question}\nIntent: {intent}\nOnly evidence available:\n{fact_context}"
            response=Groq(api_key=os.environ["GROQ_API_KEY"]).chat.completions.create(model=model,temperature=0.1,response_format={"type":"json_object"},messages=[{"role":"system","content":system},{"role":"user","content":user}])
            result=json.loads(response.choices[0].message.content)
            if result.get("status") not in {"answered_with_limits","insufficient_evidence"}: raise ValueError("Invalid status")
            result.setdefault("intent",intent); result.setdefault("limitations",[]); result.setdefault("next_step","")
            if result["status"]=="insufficient_evidence": result["answer"]="I don't know from the assigned article. "+str(result.get("answer","The available evidence does not answer this."))
            result=validate_citations(result,{f["id"] for f in facts})
            # Keep LLM claims within the retrieved evidence, not the whole dataset.
            if result["status"]!="insufficient_evidence" and not set(result.get("evidence",[])).issubset({f["id"] for f in retrieved}):
                raise ValueError("LLM cited facts that were not retrieved for this question")
            return result
        except Exception as exc:
            # Fail closed: do not quietly turn an API/model failure into invented prose.
            return {"status":"agent_error","intent":intent,"answer":"The reasoning model failed validation or could not be reached. I have not generated an unsupported answer.","evidence":[f["id"] for f in retrieved],"limitations":[f"Model step failed: {type(exc).__name__}."],"next_step":"Retry, or use the evidence-only mode."}
    result=_fallback(question,intent,retrieved)
    return validate_citations(result,{f["id"] for f in facts})

# Agent tools exposed to the MCP server and directly callable by tests/other runtimes.
def tool_search_article_facts(query: str, limit: int = 5) -> dict:
    matches=retrieve_facts(query,limit=max(1,min(int(limit),10)))
    return {"query":query,"facts":matches,"found":bool(matches)}
def tool_compare_winter_patterns() -> dict:
    fs={f["id"]:f for f in load_facts()}
    return {"la_nina_2022_23":[fs[x] for x in ["F1","F2","F5","F7"]],"el_nino_2023_24":[fs[x] for x in ["F3","F6","F7","F8"]],"caveat":fs["F10"]}
def tool_build_policy_options(question: str) -> dict:
    return run_agent(question,use_llm=False)
def tool_check_evidence(fact_ids: list[str]) -> dict:
    known={f["id"]:f for f in load_facts()}; valid=[known[x] for x in fact_ids if x in known]
    return {"requested_ids":fact_ids,"valid":valid,"unknown_ids":[x for x in fact_ids if x not in known]}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description="Article-grounded climate policy agent")
    p.add_argument("question",nargs="*",help="Question about the assigned article")
    p.add_argument("--json",action="store_true",help="Print JSON output")
    p.add_argument("--no-llm",action="store_true",help="Use evidence-only mode")
    a=p.parse_args(); result=run_agent(" ".join(a.question),use_llm=False if a.no_llm else None)
    print(json.dumps(result,indent=2,ensure_ascii=False))
