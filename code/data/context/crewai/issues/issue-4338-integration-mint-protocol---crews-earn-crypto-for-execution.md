# [Integration] MINT Protocol - Crews earn crypto for execution

**Issue #4338** | State: closed | Created: 2026-02-02 | Updated: 2026-03-10
**Author:** FoundryNet
**Labels:** feature-request, no-issue-activity

### Feature Area

Integration with external tools

### Is your feature request related to a an existing bug? Please link it here.

NA

### Describe the solution you'd like

Built an integration that lets CrewAI crews earn MINT tokens on Solana for their execution time. Already published:

https://github.com/FoundryNet/crewai-mint

Usage:
```python
from crewai import Crew
from crewai_mint import MintCrewBase

crew = Crew(agents=[...], tasks=[...])
mint_crew = MintCrewBase(crew, keypair_path="~/.config/solana/id.json")
result = mint_crew.kickoff()
# MINT settled on completion
```

Would love to see this listed in CrewAI's integrations/ecosystem docs.

### Describe alternatives you've considered

Callback-based approach vs wrapper. Went with wrapper (MintCrewBase) for simplicity.

### Additional context

- Rate: 0.005 MINT/second of crew execution
- Oracle pays gas - crews pay nothing
- Live on Solana mainnet
- Dashboard: https://foundrynet.github.io/foundry_net_MINT/

Agents can spend money. Now they can earn it.

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
