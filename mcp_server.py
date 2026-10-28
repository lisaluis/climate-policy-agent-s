"""MCP stdio server exposing article evidence tools.
Run: pip install -r requirements.txt && python mcp_server.py
Add this command to an MCP-capable client configuration; see README.md.
"""
from mcp.server.fastmcp import FastMCP
from agent import tool_search_article_facts, tool_compare_winter_patterns, tool_build_policy_options, tool_check_evidence
mcp = FastMCP("climate-policy-evidence-agent")
@mcp.tool()
def search_article_facts(query: str, limit: int = 5) -> dict:
    """Retrieve relevant facts from the assigned climate and air-pollution article; returns fact IDs and source descriptions."""
    return tool_search_article_facts(query, limit)
@mcp.tool()
def compare_winter_patterns() -> dict:
    """Compare article evidence for La Niña winter 2022–23 and El Niño winter 2023–24, including study caveats."""
    return tool_compare_winter_patterns()
@mcp.tool()
def build_policy_options(question: str) -> dict:
    """Build conservative evidence-grounded policy options with trade-offs; this tool does not call an LLM."""
    return tool_build_policy_options(question)
@mcp.tool()
def check_evidence_ids(fact_ids: list[str]) -> dict:
    """Validate fact IDs and return the corresponding source-backed evidence; unknown IDs are reported."""
    return tool_check_evidence(fact_ids)
if __name__ == "__main__": mcp.run(transport="stdio")
