# Show HN: AI agent forgets user preferences every session. This fixes it

**HN** | Points: 6 | Comments: 0 | Date: 2026-02-07
**Author:** fliellerjulian
**HN URL:** https://news.ycombinator.com/item?id=46929447
**Link:** https://www.pref0.com/

I build AI agents for work and kept hitting the same issue: a user corrects the agent, the session ends, and the correction is gone. Next session, same correction. I tracked it across our users and the average preference gets re-corrected 4+ times before people just give up.
Existing solutions don't really solve this. Memory layers store raw conversation logs. RAG retrieves documents. Neither extracts what the user actually wants as a structured, persistent preference.
So I built pref0. It does one thing: extracts structured preferences from user corrections and compounds confidence across sessions.
How it works in practice. Say you're building a customer support agent:Session 1: User says "always escalate billing issues to a human, don't try to resolve them." 
pref0 extracts billing_issues: escalate_to_human, confidence 0.55.Session 4: User flags a billing ticket the agent tried to auto-resolve. pref0 reinforces the preference. Confidence hits 0.85.Session 7: A billing issue comes in. The agent routes it to a human without being told. No correction needed.Now multiply that across hundreds of users. Each one teaching your agent slightly different things. pref0 maintains a structured profile per user (or team, or org) that your agent reads before every response.The API is intentionally minimal. Two endpoints:
POST &#x2F;track: send conversation history after a session. pref0 extracts preferences automatically.
GET &#x2F;profiles&#x2F;{user_id}: fetch learned preferences before the agent responds.A few design decisions:
> Explicit corrections ("don't do X") score higher than implied preferences. Stronger signal.
> Preferences are hierarchical: user > team > org. New team members inherit org conventions on day one.
> Confidence decays over time so stale preferences don't stick forever.This isn't a replacement for memory. Memory stores what happened. pref0 learns what the user wants. You can run both side by side.Works with LangChain, CrewAI, Vercel AI SDK, or raw API calls. Free tier available -> https:&#x2F;&#x2F;pref0.com&#x2F;docsWould love feedback on the approach, especially from anyone building agents with repeat users.
