from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    code: str
    language: str
    review_findings: List[str]
    test_code: str
    test_results: str
    final_report: str
    messages: Annotated[List[str], operator.add]
    thread_id: str
    skill_context: str
    chosen_model: str
    feedback: str
    reflection_count: int

    