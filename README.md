# Climate Policy Agent — Article C

**An article-grounded AI agent for the assignment “Study traces how an El Niño changed the pollution map”.** This repository contains only the policy agent, its tools/MCP server, skills, Python implementation, Colab notebook, and a public GitHub Pages website. It does not include the separate fine-tuned-LLM assignment.

## What makes it an agent?
It follows a workflow rather than simply chatting: **classify intent → retrieve article facts → select a task skill → optionally synthesise with an LLM → validate evidence IDs → return a structured result**. It has explicit tools, a separate MCP server, reusable skills, a refusal path for unsupported questions, and validation. Without an API key, evidence-only mode still works. With `GROQ_API_KEY` set in a trusted Python/Colab runtime, the LLM can synthesise a more natural answer—but it is restricted to retrieved facts.

## Article scope
The evidence store captures the article's two related topics: (1) PM2.5 changes in winters 2022–23 and 2023–24 and the role of winds/weather, and (2) long-term climate-zone changes and implications for agriculture. The article says the PM2.5 study covers two unusual winters and does not establish direct causality or guarantee future patterns. These caveats are part of the agent's required reasoning.

## Files
```text
index.html                 GitHub Pages website + agent UI
style.css                  Responsive visual design
website.js                 Browser agent (retrieval, evidence threshold, structured output)
agent.py                   Python agent + tools + optional Groq synthesis
mcp_server.py               MCP stdio server exposing four tools
data/facts.json             Curated facts from the assigned article
skills/*.md                 Agent skills / operating procedures
notebooks/climate_policy_agent.ipynb  Colab notebook for the same Python agent
tests/test_agent.py         Offline tests; no API key needed
requirements.txt             Optional LLM + MCP dependencies
```

## Run the Python agent locally
Python 3.10+ recommended.
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python agent.py "Why did Delhi's PM2.5 change between the two winters?" --no-llm
python agent.py "What policy options are relevant to this article?" --no-llm
pytest -q
```
To enable optional LLM synthesis in a trusted environment, set `GROQ_API_KEY` as an environment variable, then run `python agent.py "your question"`. Never commit the key. Model name can be changed with `GROQ_MODEL`.

## Google Colab notebook
Open `notebooks/climate_policy_agent.ipynb` in Colab. Upload/clone the repository, install dependencies, and run cells in order. The notebook runs without a GPU. API access is optional; if you choose to use Groq, add the key as a Colab secret named `GROQ_API_KEY`—do not type it into a public notebook cell.

## MCP server: tools
`mcp_server.py` exposes these MCP tools over stdio:
- `search_article_facts(query, limit)` — retrieve source facts and IDs.
- `compare_winter_patterns()` — compare the La Niña and El Niño winters.
- `build_policy_options(question)` — produce conservative policy options and trade-offs.
- `check_evidence_ids(fact_ids)` — validate cited fact IDs.

Install dependencies and run `python mcp_server.py` in an MCP-capable client. Example client configuration (replace the absolute path with the real path on your machine):
```json
{
  "mcpServers": {
    "climate-policy-agent": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/climate-policy-agent/mcp_server.py"]
    }
  }
}
```
MCP clients launch this local server; GitHub Pages cannot itself run a local MCP process. The browser site has equivalent in-browser evidence tools so it remains usable as a static site.

## GitHub Pages: publish the live website
1. Create a new **public** GitHub repository (e.g. `climate-policy-agent`).
2. Upload the files and folders in this repository to its root.
3. In GitHub, open **Settings → Pages**. Under Build and deployment, choose **Deploy from a branch**, branch `main`, folder `/ (root)`, and Save.
4. Wait for the deployment. The live URL will be `https://YOUR-USERNAME.github.io/climate-policy-agent/`.
5. Put the actual URL in your submission after GitHub reports the deployment as successful.

**Important hosting limit:** GitHub Pages hosts static files, not a Python process. The published website uses the in-browser evidence agent and needs no API key. The Python/Colab agent can optionally use an LLM. If you want the public website itself to call an LLM, deploy a backend separately (e.g. a server platform) and keep the API key as a server-side secret; never place secrets in GitHub Pages JavaScript.

## Agent behaviour and limitations
- Uses only the curated facts in `data/facts.json` for its grounded answers.
- For unsupported questions, it says it does not know from the assigned article.
- Cites fact IDs and exposes source descriptions.
- Separates reported findings from proposed policy options.
- The browser version uses conservative retrieval and extractive evidence summaries; the Python version can optionally use a hosted LLM.
- This is a classroom prototype, not a live AQI monitor, operational forecast, or substitute for official scientific/policy advice.

## Article source
Times of India article supplied for CSI 6007 Lab Exam, Assignment C, plus its summary of the related Atmospheric Pollution Research and IMD/IITM studies. Details and caveats in the fact store are limited to the supplied article. Verify the original papers before using the numbers in formal research.
