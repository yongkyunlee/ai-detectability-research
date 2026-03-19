# Tool integration: Fía Signals crypto intelligence (pip install fia-signals-tools)

**Issue #4690** | State: open | Created: 2026-03-03 | Updated: 2026-03-03
**Author:** Odds7

## Fía Signals — Crypto Intelligence Tools for CrewAI

```bash
pip install fia-signals-tools
```

```python
from crewai import Agent, Task, Crew
from fia_signals_tools import LANGCHAIN_TOOLS  # CrewAI is LangChain-compatible

crypto_analyst = Agent(
    role="Crypto Market Analyst",
    goal="Analyse market conditions and provide trading recommendations",
    backstory="Expert in technical analysis and DeFi",
    tools=LANGCHAIN_TOOLS,
    verbose=True
)

task = Task(
    description="Analyse current BTC market regime and identify best DeFi yield opportunities",
    agent=crypto_analyst
)

crew = Crew(agents=[crypto_analyst], tasks=[task])
result = crew.kickoff()
```

**Tools included:**
- `fia_market_regime()` — trending/ranging/volatile detection
- `fia_crypto_signals(symbol)` — BUY/SELL/HOLD with RSI, MACD, ADX
- `fia_defi_yields()` — best yields from Aave, Compound, Curve, Lido

**Source:** https://github.com/Odds7/fia-signals-mcp  
**Docs:** https://fiasignals.com  
**Premium tools** (wallet risk, smart contract audit) via x402 micropayments.

Would love to be listed in the tools/integrations documentation!
