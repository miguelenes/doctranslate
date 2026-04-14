"""Strip common LLM wrappers around JSON text."""


def clean_llm_json_text(llm_output: str) -> str:
    """Remove markdown fences and <json> wrappers."""
    llm_output = llm_output.strip()
    if llm_output.startswith("<json>"):
        llm_output = llm_output[6:]
    if llm_output.endswith("</json>"):
        llm_output = llm_output[:-7]
    if llm_output.startswith("```json"):
        llm_output = llm_output[7:]
    if llm_output.startswith("```"):
        llm_output = llm_output[3:]
    if llm_output.endswith("```"):
        llm_output = llm_output[:-3]
    return llm_output.strip()
