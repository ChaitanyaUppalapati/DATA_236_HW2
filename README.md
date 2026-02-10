# DS_HW2 - LangGraph Multi-Agent System

This repository contains the implementation of a LangGraph multi-agent system with supervisor pattern for DATA 236 Homework 2.

## Files

- `langgraph_agents.py` - Main LangGraph implementation with streaming output
- `test_correction_loop.py` - Test script demonstrating correction loop with forced reviewer issues
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Features

- Multi-agent system with Planner and Reviewer agents
- Supervisor pattern with dynamic routing
- Self-correction loop when issues are found
- Streaming output using `.stream()` method
- State management with turn counting

## Requirements

```
ollama
langgraph
langchain-core
```

## Usage

### Run the main LangGraph system:
```bash
python langgraph_agents.py
```

### Run the correction loop test:
```bash
python test_correction_loop.py
```

## How It Works

1. **Supervisor Node**: Manages turn counting and state updates
2. **Planner Node**: Creates detailed plans for tasks
3. **Reviewer Node**: Reviews plans and provides feedback
4. **Router Logic**: Decides which node to execute next based on state
5. **Correction Loop**: Routes back to planner when issues are found

## Assignment Requirements

✅ Invoked graph with initial state using `.stream()` method  
✅ Demonstrated correction loop by forcing reviewer to return issues  
✅ Graph correctly routes task back to planner when issues found  
✅ Streaming output shows each step of execution
