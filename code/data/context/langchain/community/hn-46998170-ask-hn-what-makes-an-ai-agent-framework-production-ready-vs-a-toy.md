# Ask HN: What makes an AI agent framework production-ready vs. a toy?

**HN** | Points: 5 | Comments: 1 | Date: 2026-02-13
**Author:** winclaw-dev
**HN URL:** https://news.ycombinator.com/item?id=46998170

I've been evaluating AI agent frameworks (LangChain, CrewAI, AutoGPT, OpenClaw, etc.) and I'm trying to figure out what separates the ones that actually work in production from the ones that are fun demos.My current checklist for "production-ready":1. Persistent memory across sessions (not just in-context window stuffing)
2. Real tool use with error recovery (file I&#x2F;O, shell, browser, APIs)
3. Multi-model support (swap between Claude, GPT, local models without rewriting)
4. Extensibility via a skill&#x2F;plugin system rather than hardcoded chains
5. Runs as a daemon&#x2F;service, not just a CLI you invoke manually
6. Security boundaries — sandboxing, permission models, audit logsWhat I've noticed is most frameworks nail 1-2 of these but fall apart on the rest. The ones built for demos tend to have flashy UIs but break when you try to run them unattended for a week.What's your checklist? What patterns have you seen that separate real agent infrastructure from weekend projects?

## Top Comments

**verdverm:**
I'd look to Google's ADK for what enterprise open source &#x2F; production features look like. Available in { python, java, golang, typescript } at varying levels of maturity. Work appears rapid (I maintain a fork for adk-go, which includes sandboxing, time travel, and a few bug fixes &#x2F; enhancements). Great interfaces that are easy to extend with code.https:&#x2F;&#x2F;google.github.io&#x2F;adk-docs&#x2F;get-started&#x2F;about
