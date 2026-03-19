# [FEATURE] Agents can discover & use tools/resources hosted on Model Context Protocol (MCP) Server

**Issue #1813** | State: closed | Created: 2024-12-28 | Updated: 2026-03-17
**Author:** ritzvik
**Labels:** feature-request, no-issue-activity

### Feature Area

Agent capabilities

### Is your feature request related to a an existing bug? Please link it here.

NA

### Describe the solution you'd like

Anthropic's new Model Context Protocol is been touted as "a new standard for connecting AI assistants to the systems where data lives, including content repositories, business tools, and development environments".

Here are some resources to brush up on the same:
 - https://www.anthropic.com/news/model-context-protocol
 - https://github.com/modelcontextprotocol

MCP provides specifications for both clients & servers.

The MCP server can host [3 types of primitives](https://github.com/modelcontextprotocol):
 - Tools (synonymous with CrewAI/langchain/autogen tools)
 - Resources (tools, but with no side effects, like fetching data from somewhere)
 - Prompts

Anthropic has open sourced their [python SDK](https://github.com/modelcontextprotocol/python-sdk) for making server out of tools(python functions) easily.

## Vision

 - CrewAI agents can take in MCP server address and port(apart from usual `tools`) when defining the agent.
 - The agent can discover tools/resources hosted within that MCP server
 - Use the tools as and when required(like with regular tools)

The Python-SDK also has a [lightweight client](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#writing-mcp-clients) implementation. 

A number of applications have implemented MCP clients including the Claude Desktop Application. [Here's](https://modelcontextprotocol.io/clients) the full list.

### Describe alternatives you've considered

_No response_

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**klauern:**
I would like to know if this is being pursued as an option as well.

**vivek-viswanat:**
Is there a plan to take this up?

**cheepon:**
same request +1

**curlyz:**
helpful features +1

**fsa317:**
This sounds quite helpful.

**omarcevi:**
any updates regarding this feature?

**ToruGuy:**
+1

**roribio:**
+1

**varunp2k:**
+1
