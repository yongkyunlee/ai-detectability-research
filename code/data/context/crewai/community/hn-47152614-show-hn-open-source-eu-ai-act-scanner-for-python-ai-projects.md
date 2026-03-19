# Show HN: Open-Source EU AI Act Scanner for Python AI Projects

**HN** | Points: 3 | Comments: 1 | Date: 2026-02-25
**Author:** shotwellj
**HN URL:** https://news.ycombinator.com/item?id=47152614
**Link:** https://airblackbox.ai/demo

I built an open-source CLI tool that scans Python AI projects for EU AI Act technical requirements. It checks for 6 things the regulation asks for: risk management documentation, data governance, human oversight hooks, transparency logging, accuracy&#x2F;robustness testing, and record-keeping.
Right now it detects LangChain, CrewAI, OpenAI, Anthropic, HuggingFace, and AutoGen patterns, then flags what's missing against Articles 9-15 of the Act.
It's not a legal compliance tool — it checks whether your code has the technical components the regulation references. Think of it like a linter for AI governance requirements.
The interactive demo at the link walks through a sample scan. The scanner itself is pip-installable: pip install air-compliance-checker
GitHub: https:&#x2F;&#x2F;github.com&#x2F;air-blackbox&#x2F;air-compliance-checker
Feedback welcome — especially from anyone actually dealing with EU AI Act prep.

## Top Comments

**tradeapollo:**
Mind you, that EU AI Act Scanner for Python projects is quite naive it doesn't adhere to the law by pushing code into a cloud scanner. The real deal requires local scanning to respect data sovereignty laws. For a more responsible solution, check out TradeApollo's Shadow Scout; it's self-hosted, instant connect , and plays nice with the NIST RMF without sneaking out your data."Deployment Link: https:&#x2F;&#x2F;www.tradeapollo.co&#x2F;demo
