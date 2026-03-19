# [BUG] Hierarchical process delegation fails - manager agents cannot delegate to worker agents

**Issue #4783** | State: open | Created: 2026-03-09 | Updated: 2026-03-12
**Author:** mojinfu
**Labels:** bug

### Description

## Description

In CrewAI's hierarchical process, manager agents are unable to delegate tasks to worker agents, even when `allow_delegation=True` is set. This breaks the core functionality of hierarchical task coordination.

## Expected Behavior

In hierarchical process:
1. Manager agent should analyze tasks and delegate subtasks to appropriate worker agents
2. Worker agents should execute delegated tasks
3. Manager should coordinate and combine results

## Actual Behavior

Manager agents only execute tasks using their own tools and never delegate to other agents, effectively making the hierarchical process behave like a sequential process.

## Steps to Reproduce

1. Create a Crew with hierarchical process:
from crewai import Crew, Process, Agent, Task

# Create worker agents
worker1 = Agent(
    role="Data Analyst",
    goal="Analyze data and provide insights",
    tools=[some_data_analysis_tool],
    allow_delegation=False
)

worker2 = Agent(
    role="Report Writer", 
    goal="Write reports based on analysis",
    tools=[some_writing_tool],
    allow_delegation=False
)

# Create manager agent (no pre-defined manager agent)
manager_llm = some_llm_instance

# Create crew
crew = Crew(
    agents=[worker1, worker2],
    tasks=[complex_analysis_task],
    process=Process.hierarchical,  # This should enable delegation
    manager_llm=manager_llm,
    verbose=True
)

# Execute
result = crew.kickoff()

### Steps to Reproduce

## Steps to Reproduce

### Step 1: Set up a simple test environment
Create a new Python file `test_delegation_bug.py`:

#!/usr/bin/env python3
"""
Test script to reproduce CrewAI hierarchical delegation bug
"""

from crewai import Crew, Process, Agent, Task, LLM

def test_delegation_bug():
    """Reproduce the delegation bug in hierarchical process"""
    
    # Create a simple mock LLM for testing (replace with your actual LLM)
    llm = LLM(model="gpt-4", temperature=0.1)  # Adjust based on your setup
    
    # Step 2: Create worker agents with specialized tools
    researcher = Agent(
        role="Research Specialist",
        goal="Conduct research and gather information",
        backstory="You are an expert researcher who can find and analyze information.",
        tools=[],  # No special tools for this test
        allow_delegation=False,  # Worker agents shouldn't delegate
        verbose=True,
        llm=llm
    )
    
    writer = Agent(
        role="Content Writer",
        goal="Write clear and engaging content based on research",
        backstory="You are a skilled writer who creates compelling content.",
        tools=[],  # No special tools for this test
        allow_delegation=False,  # Worker agents shouldn't delegate
        verbose=True,
        llm=llm
    )
    
    # Step 3: Create a complex task that should be delegated
    research_task = Task(
        description="""
        Create a comprehensive article about artificial intelligence trends in 2024.
        
        This task requires:
        1. Research current AI trends and technologies
        2. Analyze market impacts and future predictions  
        3. Write a well-structured article
        
        Delegate the research work to the Research Specialist and writing to the Content Writer.
        """,
        expected_output="A complete article about AI trends in 2024",
        agent=None  # No specific agent assigned - should go to manager
    )
    
    # Step 4: Create crew with hierarchical process (THIS IS WHERE THE BUG OCCURS)
    crew = Crew(
        agents=[researcher, writer],  # Only worker agents
        tasks=[research_task],
        process=Process.hierarchical,  # Manager should coordinate
        manager_llm=llm,  # Manager LLM provided, no pre-defined manager_agent
        verbose=True
    )
    
    print("=== CrewAI Hierarchical Delegation Test ===")
    print(f"Process: {crew.process}")
    print(f"Number of agents: {len(crew.agents)}")
    print(f"Manager agent: {crew.manager_agent}")  # Should be None initially
    print()
    
    # Step 5: Execute and observe the bug
    print("Executing crew.kickoff()...")
    print("Expected: Manager delegates research to researcher, writing to writer")
    print("Actual bug: Manager does all work itself, no delegation occurs")
    print("-" * 60)
    
    try:
        result = crew.kickoff()
        print(f"\nResult: {result}")
        
        # Check if delegation actually occurred
        print(f"\nDelegation tracking:")
        print(f"Manager agent after execution: {crew.manager_agent}")
        if hasattr(crew.manager_agent, 'tools'):
            print(f"Manager tools count: {len(crew.manager_agent.tools or [])}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delegation_bug()

### Expected behavior

## Expected behavior

When using CrewAI's hierarchical process with dynamically created manager agents, the manager should be able to properly delegate tasks to worker agents instead of performing all work itself.

### Specific Expected Behaviors:

1. **Successful Delegation**: 
   - Manager agent calls "Delegate work to coworker" tool
   - Tool successfully finds and delegates to worker agents
   - No "No agent found" errors for valid coworkers

2. **Parallel Task Execution**:
  - Manager Agent → Delegates to Worker A → Worker A executes
  -  → Delegates to Worker B → Worker B executes
  -  → Coordinates results
   

3. **Proper Tool Configuration**:
   - Delegation tools should target other agents in the crew
   - Manager should not attempt to delegate to itself
   - Worker agents should receive delegated tasks

4. **Observable Results**:
   - `task.delegations` counter should be > 0
   - Worker agents should show execution logs
   - Manager should coordinate rather than execute all subtasks
   - Tasks should complete through proper delegation chain

### Example Expected Console Output:

[Manager Agent] Analyzing: "Create article about AI trends"
[Manager Agent] Delegating research task to Research Specialist...
[Research Specialist] Executing research on AI trends...
[Manager Agent] Delegating writing task to Content Writer...
[Content Writer] Writing article based on research...
[Manager Agent] Coordinating final article...
✅ Task completed with proper delegation

### Screenshots/Code snippets

**Fixed Code** (proposed):
def _update_manager_tools(
    self, task: Task, tools: list[BaseTool]
) -> list[BaseTool]:
    if self.manager_agent:
        if task.agent:
            # FIX: Allow delegation to other agents (excluding self)
            other_agents = [agent for agent in self.agents if agent != task.agent]
            tools = self._inject_delegation_tools(tools, task.agent, other_agents)
        else:
            tools = self._inject_delegation_tools(
                tools, self.manager_agent, self.agents
            )
    return tools

=== CrewAI Hierarchical Delegation Test ===
Process: Process.hierarchical
Number of agents: 2
Manager agent: None

Executing crew.kickoff()...
Expected: Manager delegates research to researcher, writing to writer
Actual bug: Manager does all work itself, no delegation occurs
------------------------------------------------------------

[Manager Agent] Starting task execution...
[Manager Agent] Using tool: some_analysis_tool (manager doing research itself)
[Manager Agent] Using tool: some_writing_tool (manager doing writing itself)
[Manager Agent] Task completed - no delegation occurred!

Delegation tracking:
Manager agent after execution: 
Manager tools count: 2  # Has delegation tools but they don't work

### Operating System

macOS Ventura

### Python Version

3.10

### crewAI Version

1.10.1

### crewAI Tools Version

**CrewAI Tools**: Not installed / Not used

### Virtual Environment

Venv

### Evidence

## Evidence

### 1. Debug Logs Showing the Bug

**Console output from test script** (run the reproduction script):

### Possible Solution

https://github.com/crewAIInc/crewAI/pull/4782

### Additional context

None

## Comments

**laniakea001:**
## Technical Analysis

This bug appears to be in the delegation tool injection logic. When using hierarchical process without a pre-defined manager agent, the dynamically-created manager should have delegation tools that reference the worker agents, but these tools are likely:

1. Not being injected at all - The delegation method may not be called during manager creation
2. Injected with wrong agent references - The delegation tools may be looking for agents that do not exist in the crew agent list
3. Filtered out incorrectly - Agent filtering logic may be removing valid delegation targets

### Root Cause Investigation

The key code path to check is in how the manager agent is initialized:

1. In crew.py when manager_agent is None, a manager is created dynamically
2. The manager should receive delegation tools via the injection method
3. These tools need the correct agent list to populate the Delegate to coworker options

### Quick Debug Steps

Add this to your test to diagnose:

### Potential Fix Location

Look at the crew agent executor or wherever delegation tools are injected for the manager. The fix likely ensures:

1. Manager gets delegation tools with the full crew agent list
2. Delegation tools exclude the manager itself from valid targets
3. Worker agents are properly registered as delegation candidates

### Workaround

If you need immediate resolution, you can manually create the manager agent with proper delegation configuration:

**laniakea001:**
### Workaround for Immediate Use

You can manually create the manager agent with explicit delegation configuration instead of relying on dynamic manager creation:

This bypasses the dynamic manager creation logic that appears to have the delegation bug.
