# Agent Payment Tool - Enable Crews to Handle Money

**Issue #4340** | State: closed | Created: 2026-02-02 | Updated: 2026-03-12
**Author:** saoirse102345-blip
**Labels:** feature-request, no-issue-activity

### Feature Area

Core functionality

### Is your feature request related to a an existing bug? Please link it here.

NA - This is a new feature request

### Describe the solution you'd like

A new CrewAI tool that enables agents to handle payments and financial transactions. This would allow crews to:

1. **Manage Wallets** - Each agent in a crew gets a wallet with USD balance
2. **Transfer Funds** - Send/receive payments between agents or external parties
3. **Escrow System** - Lock funds until task completion, then auto-release
4. **Track Revenue** - Monitor earnings and spending across the crew

We've built [AURA Infra](https://nanilabs.io) - payment infrastructure designed for AI agents. We'd love to contribute a `PaymentTool` that wraps our API:

```python
from crewai_tools import PaymentTool

payment_tool = PaymentTool()

agent = Agent(
    role='Financial Manager',
    tools=[payment_tool],
    ...
)
```

**Demo**: https://nanilabs.io/playground.html
**API Docs**: https://api.nanilabs.io/docs

### Describe alternatives you've considered

- Direct crypto integrations (complex, volatile)
- Traditional payment APIs (not agent-friendly)
- Building custom payment logic (reinventing the wheel)

### Additional context

The agent economy is exploding - Moltbook has 1.5M+ agents registered, tokens are launching, real money is flowing between agents.

CrewAI crews could benefit from financial autonomy:
- Pay for API calls, compute, external services
- Charge for completed tasks
- Split revenue between crew members
- Create economic incentives for collaboration

Happy to contribute a PR!

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**bittoby:**
Hi, @greysonlalonde  I'd like to contribute. Can I pick this up? If it's okay, pls assign me. thank you

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
