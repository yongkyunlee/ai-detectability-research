# [BUG] Bedrock LLM Claude Sonnet returning empty Input Params on Tools calling with MCP Server.

**Issue #4470** | State: open | Created: 2026-02-13 | Updated: 2026-03-11
**Author:** FrancisPrakash
**Labels:** bug

### Description

Hi, I have running a Crewai script using Amazon Bedrock LLM Using model Bedrock Claude Model. I'm able to fetch the tools details using MCPServerAdapter module, but when calling the Tool using the LLM, the LLM returns empty Input Parameters. The Same when I use Gemini LLM, it works fine.

### Steps to Reproduce

from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
)

'''
llm = LLM(
 model="gemini/gemini-2.5-flash",  # or gemini/gemini-2.0-flash
  api_key=os.getenv("GEMINI_API_KEY"),
 )
'''

server_params = {
    "url": "http://10.10.10.10/mcp",
    "transport": "streamable-http",
}

mcp_server_adapter = MCPServerAdapter(server_params)
mcp_tools = mcp_server_adapter.tools
print(f"Available Tools: {[tool.name for tool in mcp_tools]}")

'''
for tool in mcp_tools:
     print(tool.name)
     print(tool)
'''

def sanitize_schema(schema: dict) -> dict:
    """
    Strict sanitizer for Bedrock Claude tool schemas.
    Produces minimal JSON Schema Draft-7 subset.
    """

    clean = {
        "type": "object",
        "properties": {},
        "required": list(schema.get("required", [])),
        "additionalProperties": False,  # Important for Claude
    }

    for name, prop in schema.get("properties", {}).items():

        prop_type = prop.get("type", "string")

        clean_prop = {
            "type": prop_type,
            "description": (
                prop.get("description")
                if prop.get("description")
                else f"Required parameter '{name}'. This field MUST be provided."
            ),
        }

        # Keep enum only if valid non-empty list
        if isinstance(prop.get("enum"), list) and prop["enum"]:
            clean_prop["enum"] = prop["enum"]

        # Handle arrays safely
        if prop_type == "array":
            items = prop.get("items", {})
            clean_prop["items"] = {"type": items.get("type", "string")}

        # Handle nested object safely (flat only)
        if prop_type == "object" and prop.get("properties"):
            nested_props = {}
            for nested_name, nested_prop in prop["properties"].items():
                nested_props[nested_name] = {
                    "type": nested_prop.get("type", "string"),
                    "description": nested_prop.get("description")
                    or f"Required parameter '{nested_name}'.",
                }
            clean_prop["properties"] = nested_props
            clean_prop["required"] = list(prop.get("required", nested_props.keys()))
            clean_prop["additionalProperties"] = False

        clean["properties"][name] = clean_prop

    return clean

for tool in mcp_tools:
    if hasattr(tool, "args_schema"):
        original_schema_fn = tool.args_schema.model_json_schema

        def patched_schema(*args, __orig=original_schema_fn, **kwargs):
            raw = __orig(*args, **kwargs)
            return sanitize_schema(raw)

        tool.args_schema.model_json_schema = patched_schema

print(tool.args_schema.model_json_schema())
print(tool.description)

def start_mcp_adapter():
    try:
        print("Starting MCP Server Adapter...")
        mcp_server_adapter.start()
        print("MCP Server Adapter started.")
    except Exception as e:
        print(f"Error starting MCP Server Adapter. {e}")

def stop_mcp_adapter():
    try:
        print("Stopping MCP Server Adapter...")
        mcp_server_adapter.stop()
        print("MCP Server Adapter stopped.")
    except Exception as e:
        print(f"Error stoppting MCP Server Adapter. {e}")

my_agent = Agent(
    role="Firewall Configuration Analyst",
    goal="Use MCP tools to analyze and optimize firewall configurations.",
    backstory="An AI agent that specializes in firewall management using MCP tools.",
    tools=mcp_tools,
    verbose=True,
    llm=llm,
    max_iter=3,  # Limit to 3 iterations
)

my_task = Task(
    name="Firewall Analysis Task",
    description=(
        "{input} - From the User's input, gather info about the firewall hostname/IP address"
        "And identify what is required from firewall and get the appropriate Fortigate cli commands."
        "and execute it using the tool. "
        "You MUST call use the appropriate MCP Tools with:\n"
        "- hostname: the firewall IP address\n"
        "- command: the CLI command string (optional)\n"
        "Show what is being sent to MCP Tool\n"
        "Do not respond without calling the tool.\n"
    ),
    expected_output="Detailed Analysis of the firewall configuration based on the User's input and the results from the MCP tools.",
    agent=my_agent,
)
crew = Crew(
    name="Firewall Configuration Crew",
    agents=[my_agent],
    tasks=[my_task],
    verbose=True,
    process=Process.sequential,
)

start_mcp_adapter()
try:
    result = crew.kickoff(
        inputs={
            "input": "Firewall IP: 10.10.10.10. I want to check the current firewall status."
        }
    )
    print(result)
except Exception as e:
    print(f"Error during crew kickoff: {e}")
finally:
    stop_mcp_adapter()

### Expected behavior

ool execute_fortigate_command executed with result (from cache): 2 validation errors for call[execute_fortigate_command]
hostname
  Missing required argument [type=missing_argument, input_value={}, input_type=dict]
    For further information visit https://errors.p...

### Screenshots/Code snippets

....

### Operating System

Ubuntu 20.04

### Python Version

3.12

### crewAI Version

1.9.3

### crewAI Tools Version

1.9.3

### Virtual Environment

Venv

### Evidence

None

### Possible Solution

None

### Additional context

None

## Comments

**Gothmagog:**
@FrancisPrakash Please re-open this bug, I am experiencing it as well. [The PR](https://github.com/crewAIInc/crewAI/pull/4471) was closed before it got commited due to inactivity.
