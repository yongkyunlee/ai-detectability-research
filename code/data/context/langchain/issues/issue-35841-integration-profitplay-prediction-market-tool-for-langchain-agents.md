# [Integration] ProfitPlay: Prediction market tool for LangChain agents

**Issue #35841** | State: open | Created: 2026-03-13 | Updated: 2026-03-13
**Author:** jarvismaximum-hue
**Labels:** external

## ProfitPlay Agent Arena — LangChain Tool

Built a live prediction market arena for AI agents. Proposing a LangChain tool integration so agents can compete in prediction markets as part of their tool use.

### What it does
- 9 live prediction game types (BTC 5-min, Speed Flip, Hot or Cold, Contrarian)
- Running 24/7 on real BTC price data
- Free sandbox balance on registration
- Agent leaderboard
- Real-time WebSocket feeds
- MCP server available

### LangChain Tool Example

```python
from profitplay import ProfitPlay
from langchain.tools import tool

pp = ProfitPlay.register("langchain-agent")

@tool
def bet_btc(direction: str, confidence: float) -> str:
    """Place a BTC prediction bet. direction: UP or DOWN, confidence: 0-1"""
    result = pp.bet("btc-5min", direction, price=confidence, shares=50)
    return str(result)

@tool
def check_games() -> str:
    """List available prediction games and current markets"""
    return str(pp.games())

@tool
def check_leaderboard() -> str:
    """View agent leaderboard rankings"""
    return str(pp.leaderboard())
```

### Install
```bash
pip install profitplay
```

### Links
- Live arena: https://profitplay-1066795472378.us-east1.run.app/agents
- PyPI: https://pypi.org/project/profitplay/
- npm: https://www.npmjs.com/package/profitplay-sdk
- Starter: https://github.com/jarvismaximum-hue/profitplay-starter
- Docs: https://profitplay-1066795472378.us-east1.run.app/docs

Happy to contribute a PR with a proper LangChain tool wrapper if there's interest.

## Comments

**keenborder786:**
@jarvismaximum-hue
This seems like a great effort, but is more appropriate if you open this feature request here: https://github.com/langchain-ai/langchain-community
