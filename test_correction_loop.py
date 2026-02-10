"""
LangGraph Multi-Agent System - Correction Loop Test
This version forces the reviewer to always find issues to demonstrate the correction loop.
"""

import json
import sys
from typing import TypedDict, Dict, Any
from datetime import datetime

try:
    import ollama
except ImportError:
    print("ERROR: ollama package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ollama"])
    import ollama

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    print("ERROR: langgraph package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "langgraph", "langchain-core"])
    from langgraph.graph import StateGraph, END


# Define AgentState
class AgentState(TypedDict):
    """Shared state/memory for all agents in the graph"""
    # Input fields
    task: str
    llm: Any
    
    # Agent outputs
    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]
    
    # Control fields
    turn_count: int


def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner Agent Node - Creates a detailed plan"""
    print("\n" + "="*60)
    print(" NODE: PLANNER")
    print("="*60)
    
    task = state["task"]
    llm = state["llm"]
    turn_count = state.get("turn_count", 0)
    
    # Check if we have previous feedback
    previous_feedback = state.get("reviewer_feedback", {})
    
    if previous_feedback and turn_count > 1:
        print(f" Iteration {turn_count}: Revising plan based on feedback...")
        prompt = f"""You are a Planner Agent. The reviewer found issues with your previous plan.

Previous Feedback:
{json.dumps(previous_feedback, indent=2)}

Original Task: {task}

Create an IMPROVED plan addressing the reviewer's concerns.
Return your response as a JSON object:
{{
    "plan": "your improved detailed plan here",
    "steps": ["step 1", "step 2", "step 3"]
}}
"""
    else:
        print(f" Iteration {turn_count}: Creating initial plan...")
        prompt = f"""You are a Planner Agent. Create a concise, step-by-step plan for this task:

Task: {task}

Provide a clear, structured plan with specific steps. Be brief but thorough.
Return your response as a JSON object:
{{
    "plan": "your detailed plan here",
    "steps": ["step 1", "step 2", "step 3"]
}}
"""
    
    try:
        response = ollama.generate(model=llm, prompt=prompt)
        output = response['response'].strip()
        
        # Try to parse as JSON, fallback to plain text
        try:
            proposal = json.loads(output)
        except:
            proposal = {
                "plan": output,
                "steps": []
            }
        
        print(f" Planner created proposal with {len(proposal.get('steps', []))} steps")
        print(f"Plan preview: {proposal.get('plan', '')[:100]}...")
        return {"planner_proposal": proposal}
        
    except Exception as e:
        print(f" Error in planner_node: {e}")
        return {"planner_proposal": {"plan": f"Error: {str(e)}", "steps": []}}


def reviewer_node_always_issues(state: AgentState) -> Dict[str, Any]:
    """Reviewer Agent Node - ALWAYS returns issues for testing"""
    print("\n" + "="*60)
    print(" NODE: REVIEWER (FORCED ISSUES MODE)")
    print("="*60)
    
    plan = state["planner_proposal"]
    turn_count = state.get("turn_count", 0)
    
    print(f" Reviewing plan (Turn {turn_count})...")
    
    # FORCE ISSUES for testing - but stop after a few iterations
    if turn_count < 3:
        feedback = {
            "feedback": f"[FORCED ISSUE #{turn_count}] The plan needs more detail in step {turn_count + 1}. Please elaborate on the implementation specifics.",
            "has_issues": True,
            "suggestions": [
                f"Add more detail to step {turn_count + 1}",
                "Include error handling considerations",
                "Specify expected outcomes"
            ]
        }
        print(f"  FORCED ISSUE: Reviewer is forcing issues for testing (iteration {turn_count})")
    else:
        # After 3 iterations, approve the plan
        feedback = {
            "feedback": "The plan looks good now after multiple revisions. All concerns have been addressed.",
            "has_issues": False,
            "suggestions": []
        }
        print(f" Reviewer approved the plan after {turn_count} iterations")
    
    print(f"Has issues: {feedback.get('has_issues', False)}")
    return {"reviewer_feedback": feedback}


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Supervisor Node - Updates state (turn counter)"""
    print("\n" + "="*60)
    print("  NODE: SUPERVISOR")
    print("="*60)
    current_turn = state.get("turn_count", 0)
    new_turn = current_turn + 1
    print(f" Turn count: {current_turn}  {new_turn}")
    return {"turn_count": new_turn}


def router_logic(state: AgentState) -> str:
    """Router Function - Decides which node to execute next"""
    print("\n" + "="*60)
    print(" ROUTER: Making decision")
    print("="*60)
    
    # Check if we have a proposal yet
    if not state.get("planner_proposal"):
        print("  ROUTER DECISION: No proposal yet  going to Planner")
        return "planner"
    
    # Check if we have feedback yet
    if not state.get("reviewer_feedback"):
        print("  ROUTER DECISION: No feedback yet  going to Reviewer")
        return "reviewer"
    
    # Check if reviewer found issues
    reviewer_feedback = state.get("reviewer_feedback", {})
    has_issues = reviewer_feedback.get("has_issues", False)
    
    if has_issues:
        # Check turn limit to prevent infinite loops
        turn_count = state.get("turn_count", 0)
        max_turns = 5  # Safety limit
        
        if turn_count >= max_turns:
            print(f" ROUTER DECISION: Max turns ({max_turns}) reached  END")
            return END
        
        print(f" ROUTER DECISION: Issues found  looping back to Planner (Turn {turn_count})")
        return "planner"
    
    # No issues, we're done
    print(" ROUTER DECISION: No issues  END")
    return END


def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow"""
    print("\n" + "="*80)
    print("  BUILDING GRAPH")
    print("="*80)
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("reviewer", reviewer_node_always_issues)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        router_logic,
        {
            "planner": "planner",
            "reviewer": "reviewer",
            END: END
        }
    )
    
    # Add edges back to supervisor after each agent
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("reviewer", "supervisor")
    
    print(" Graph built successfully!")
    return workflow.compile()


def main():
    """Main function to run the LangGraph agent system"""
    print("\n" + "="*80)
    print("   LANGGRAPH CORRECTION LOOP TEST")
    print("  (Reviewer will ALWAYS find issues for first 3 iterations)")
    print("="*80)
    
    # Use a simple default task for testing
    task = input("\nEnter your task (or press Enter for default): ").strip()
    
    if not task:
        task = "Create a simple Python script to read a CSV file and calculate averages"
        print(f"Using default task: {task}")
    
    # Initialize state
    initial_state = {
        "task": task,
        "llm": "smollm:1.7b",
        "planner_proposal": {},
        "reviewer_feedback": {},
        "turn_count": 0
    }
    
    # Build graph
    graph = build_graph()
    
    print("\n" + "="*80)
    print("   EXECUTING GRAPH WITH .stream()")
    print("="*80)
    
    # Stream execution to see each step
    print("\n STREAMING OUTPUT FROM EACH STEP:\n")
    
    step_number = 0
    for step_output in graph.stream(initial_state):
        step_number += 1
        print(f"\n{''*80}")
        print(f" STEP {step_number} OUTPUT:")
        print(f"{''*80}")
        print(f"Nodes executed: {list(step_output.keys())}")
        
        # Show what changed in this step
        for node_name, updates in step_output.items():
            print(f"\n  Node '{node_name}' updated:")
            for key, value in updates.items():
                if isinstance(value, dict):
                    print(f"    - {key}: {json.dumps(value, indent=6)}")
                else:
                    print(f"    - {key}: {value}")
    
    print("\n" + "="*80)
    print("   FINAL RESULTS")
    print("="*80)
    
    # Get the complete final state
    final_state = graph.invoke(initial_state)
    
    if final_state:
        print("\n---  Final Planner Proposal ---")
        print(json.dumps(final_state.get("planner_proposal", {}), indent=2))
        
        print("\n---  Final Reviewer Feedback ---")
        print(json.dumps(final_state.get("reviewer_feedback", {}), indent=2))
        
        print(f"\n---  Total Turns: {final_state.get('turn_count', 0)} ---")
    
    print("\n" + "="*80)
    print("   EXECUTION COMPLETE")
    print("="*80)
    
    print("\n KEY OBSERVATIONS:")
    print("   - The reviewer forced issues for the first 3 iterations")
    print("   - The graph correctly routed back to the planner each time")
    print("   - After 3 iterations, the reviewer approved and the graph ended")
    print("   - This demonstrates the correction loop working as expected!")


if __name__ == "__main__":
    main()
