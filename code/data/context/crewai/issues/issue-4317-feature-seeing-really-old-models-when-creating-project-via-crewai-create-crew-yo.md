# [FEATURE] seeing really old models when creating project via "crewai create crew <your_project_name>"

**Issue #4317** | State: open | Created: 2026-01-31 | Updated: 2026-03-01
**Author:** 23f2005639
**Labels:** feature-request

### Feature Area

Core functionality

### Is your feature request related to a an existing bug? Please link it here.

Whenever i configure crewai project via this cmd "crewai create crew " I see really old models like GPT 4 or sonnet 3 and the latest ones are not there.

### Describe the solution you'd like

two things we can do 
1.Modify the code to fetch models dynamically even for predefined providers
2. Update the hard coded values as they are really old now

### Describe alternatives you've considered

_No response_

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**Br1an67:**
I'd like to work on this. Updated the hardcoded model lists for OpenAI (added o3, o4-mini, gpt-4.1-mini/nano), Anthropic (added claude-sonnet-4-5, claude-3-7-sonnet, claude-3-5-sonnet v2, claude-3-5-haiku), Groq (added llama-3.3), and Ollama (added llama3.2, llama3.3, deepseek-r1).

PR: #4663
