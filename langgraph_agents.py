"""
LangGraph Multi-Agent System with Supervisor Pattern
Refactored from sequential Ollama agent system to use stateful graph with dynamic routing.
Based on assignment instructions for DS_HW2.
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


# Step 2: Define AgentState
class AgentState(TypedDict):
    """Shared state/memory for all agents in the graph"""
    # Input fields
    title: str
    content: str
    email: str
    strict: bool
    task: str
    llm: Any
    
    # Agent outputs
    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]
    
    # Control fields
    turn_count: int


# Step 3: Creating Agent Nodes

def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner Agent Node - Creates a detailed plan"""
    print("---NODE: Planner---")
    
    task = state["task"]
    llm = state["llm"]
    
    prompt = f"""You are a Planner Agent. Create a concise, step-by-step plan for this task:

Task: {task}

Provide a clear, structured plan with specific steps. Be brief but thorough.
Return your response as a JSON object with the following structure:
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
        
        print(f"Planner created proposal with {len(proposal.get('steps', []))} steps")
        return {"planner_proposal": proposal}
        
    except Exception as e:
        print(f"Error in planner_node: {e}")
        return {"planner_proposal": {"plan": f"Error: {str(e)}", "steps": []}}


def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """Reviewer Agent Node - Reviews and critiques the plan"""
    print("---NODE: Reviewer---")
    
    plan = state["planner_proposal"]
    llm = state["llm"]
    strict = state.get("strict", False)
    
    prompt = f"""You are a Reviewer Agent. Review this plan and provide constructive feedback:

PLAN:
{json.dumps(plan, indent=2)}

Provide:
1. What's good
2. What could be improved
3. Whether there are any issues that need fixing

Return your response as a JSON object:
{{
    "feedback": "your detailed feedback here",
    "has_issues": true/false,
    "suggestions": ["suggestion 1", "suggestion 2"]
}}

Be {"very strict and critical" if strict else "balanced and constructive"}.
"""
    
    try:
        response = ollama.generate(model=llm, prompt=prompt)
        output = response['response'].strip()
        
        # Try to parse as JSON
        try:
            feedback = json.loads(output)
        except:
            # Fallback structure
            feedback = {
                "feedback": output,
                "has_issues": False,
                "suggestions": []
            }
        
        print(f"Reviewer found issues: {feedback.get('has_issues', False)}")
        return {"reviewer_feedback": feedback}
        
    except Exception as e:
        print(f"Error in reviewer_node: {e}")
        return {"reviewer_feedback": {"feedback": f"Error: {str(e)}", "has_issues": False, "suggestions": []}}


# Step 4: Building the Supervisor

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Supervisor Node - Updates state (turn counter)"""
    print("---NODE: Supervisor---")
    current_turn = state.get("turn_count", 0)
    new_turn = current_turn + 1
    print(f"Turn count: {current_turn} -> {new_turn}")
    return {"turn_count": new_turn}


def router_logic(state: AgentState) -> str:
    """Router Function - Decides which node to execute next"""
    print("---ROUTER: Making decision---")
    
    # Check if we have a proposal yet
    if not state.get("planner_proposal"):
        print("ROUTER: No proposal yet -> going to Planner")
        return "planner"
    
    # Check if we have feedback yet
    if not state.get("reviewer_feedback"):
        print("ROUTER: No feedback yet -> going to Reviewer")
        return "reviewer"
    
    # Check if reviewer found issues
    reviewer_feedback = state.get("reviewer_feedback", {})
    has_issues = reviewer_feedback.get("has_issues", False)
    
    if has_issues:
        # Check turn limit to prevent infinite loops
        turn_count = state.get("turn_count", 0)
        max_turns = 5  # Safety limit
        
        if turn_count >= max_turns:
            print(f"ROUTER: Max turns ({max_turns}) reached -> END")
            return END
        
        print("ROUTER: Issues found -> looping back to Planner")
        return "planner"
    
    # No issues, we're done
    print("ROUTER: No issues -> END")
    return END


# Step 5: Assembling the Graph

def build_graph() -> StateGraph:
    """Build and compile the LangGraph workflow"""
    print("\n=== Building Graph ===")
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("reviewer", reviewer_node)
    
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
    
    print("Graph built successfully!")
    return workflow.compile()


# Step 6: Running and Testing

def main():
    """Main function to run the LangGraph agent system"""
    print("\n" + "=" * 80)
    print("  LANGGRAPH MULTI-AGENT SYSTEM WITH SUPERVISOR PATTERN")
    print("=" * 80)
    
    # Get task from user
    task = input("\nEnter your task: ").strip()
    
    if not task:
        print("No task provided. Exiting.")
        return
    
    # Ask if strict mode
    strict_input = input("Use strict review mode? (y/n): ").strip().lower()
    strict = strict_input == 'y'
    
    # Initialize state
    initial_state = {
        "title": "LangGraph Agent Task",
        "content": task,
        "email": "user@example.com",
        "strict": strict,
        "task": task,
        "llm": "smollm:1.7b",
        "planner_proposal": {},
        "reviewer_feedback": {},
        "turn_count": 0
    }
    
    # Build graph
    graph = build_graph()
    
    print("\n" + "=" * 80)
    print("  EXECUTING GRAPH")
    print("=" * 80)
    
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
    
    # Get the complete final state
    print("\n" + "=" * 80)
    print("  GETTING FINAL STATE")
    print("=" * 80)
    final_state = graph.invoke(initial_state)
    
    # Display final results
    print("\n" + "=" * 80)
    print("  FINAL RESULTS")
    print("=" * 80)
    
    if final_state:
        print("\n--- Final Planner Proposal ---")
        print(json.dumps(final_state.get("planner_proposal", {}), indent=2))
        
        print("\n--- Final Reviewer Feedback ---")
        print(json.dumps(final_state.get("reviewer_feedback", {}), indent=2))
        
        print(f"\n--- Total Turns: {final_state.get('turn_count', 0)} ---")
    
    print("\n" + "=" * 80)
    print("  EXECUTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
