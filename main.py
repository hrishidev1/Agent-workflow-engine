from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid

app = FastAPI(title="Agent Workflow Engine")

# In-memory storage
graphs = {}
runs = {}

class State(BaseModel):
    code: str = ""
    functions: List[str] = []
    issues: List[str] = []
    quality_score: int = 50
    suggestions: List[str] = []
    iteration: int = 0

# Tools / Nodes
def extract_functions(state: Dict):
    state["functions"] = ["login()", "process_payment()", "send_email()", "calculate_tax()"]
    print("Extracted 4 functions")

def check_issues(state: Dict):
    issues = []
    if "process_payment" in " ".join(state["functions"]):
        issues.append("Payment logic mixed with others")
    if len(state["functions"]) > 3:
        issues.append("Too many functions in one file")
    state["issues"] = issues
    state["quality_score"] -= len(issues) * 15

def give_suggestions(state: Dict):
    if state["issues"]:
        state["suggestions"].append("Split payment logic into separate service")
        state["suggestions"].append("Follow Single Responsibility Principle")
        state["quality_score"] += 20
    state["iteration"] += 1
    print(f"Improved! New score: {state['quality_score']}")

TOOLS = {
    "extract": extract_functions,
    "check": check_issues,
    "suggest": give_suggestions
}

# Hard-coded workflow (Code Review Agent)
CODE_REVIEW_GRAPH = {
    "start": "extract",
    "extract": "check",
    "check": "suggest",
    "suggest": "check",   # loop back
}

graph_id = "code-review-1"
graphs[graph_id] = CODE_REVIEW_GRAPH

# Runner
def run_workflow(graph_id: str, initial_state: Dict) -> str:
    run_id = str(uuid.uuid4())[:8]
    state = initial_state.copy()
    logs = []

    current = "start"
    while current and state["iteration"] < 5:
        next_node = graphs[graph_id].get(current)

        if next_node and next_node in TOOLS:
            logs.append(f"Running {next_node}")
            TOOLS[next_node](state)
            logs.append(f"Quality score = {state['quality_score']}")

        if state["quality_score"] >= 80:
            logs.append("Quality is good! Stopping.")
            break

        current = next_node

    runs[run_id] = {"state": state, "logs": logs}
    return run_id

# APIs
@app.post("/run")
def start_run():
    initial = State(code="some python code").dict()
    run_id = run_workflow(graph_id, initial)
    return {"run_id": run_id, "message": "Code review started!"}

@app.get("/result/{run_id}")
def get_result(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, "Run not found")
    return runs[run_id]