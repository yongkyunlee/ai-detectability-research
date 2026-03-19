# Beginner help: “council of agents” with CrewAI for workout/nutrition recommendations

**r/crewai** | Score: 3 | Comments: 3 | Date: 2026-02-15
**Author:** AdhesivenessGrand254
**URL:** https://www.reddit.com/r/crewai/comments/1r5bdb6/beginner_help_council_of_agents_with_crewai_for/

Hey everyone — I’m brand new to CrewAI and I don’t really have coding skills yet.

I want to build a small “council of agents” that helps me coordinate workout / nutrition / overall health. The agents shouldn’t do big tasks (no web browsing, no automations). I mainly want them to discuss tradeoffs (e.g., recovery vs. intensity, calories vs. performance) and then an orchestrator agent summarizes it into my “recommendations for the day.”

Data-wise: ideally it pulls from Garmin + Oura, but I’m totally fine starting with manual input (sleep score, HRV, resting HR, steps, yesterday’s workout, weight, etc.).

Questions:

	•	What’s the most efficient way to set this up in CrewAI as a total beginner?

	•	Is there a simple “multi-agent discussion → orchestrator summary” pattern you’d recommend?

	•	Any tips to minimize cost (cheap models, token-saving prompts, local vs cloud), since this is mostly a fun learning project?

If you have any tips or guidance, that would be amazing. Thanks!
