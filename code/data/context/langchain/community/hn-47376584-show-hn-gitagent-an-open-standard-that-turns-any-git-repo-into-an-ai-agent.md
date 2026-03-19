# Show HN: GitAgent – An open standard that turns any Git repo into an AI agent

**HN** | Points: 147 | Comments: 39 | Date: 2026-03-14
**Author:** sivasurend
**HN URL:** https://news.ycombinator.com/item?id=47376584
**Link:** https://www.gitagent.sh/

We built GitAgent because we kept seeing the same problem: every agent framework defines agents differently, and switching frameworks means rewriting everything.GitAgent is a spec that defines an AI agent as files in a git repo.Three core files — agent.yaml (config), SOUL.md (personality&#x2F;instructions), and SKILL.md (capabilities) — and you get a portable agent definition that exports to Claude Code, OpenAI Agents SDK, CrewAI, Google ADK, LangChain, and others.What you get for free by being git-native:1. Version control for agent behavior (roll back a bad prompt like you'd revert a bad commit)
2. Branching for environment promotion (dev → staging → main)
3. Human-in-the-loop via PRs (agent learns a skill → opens a branch → human reviews before merge)
4. Audit trail via git blame and git diff
5. Agent forking and remixing (fork a public agent, customize it, PR improvements back)
6. CI&#x2F;CD with GitAgent validate in GitHub ActionsThe CLI lets you run any agent repo directly:npx @open-gitagent&#x2F;gitagent run -r https:&#x2F;&#x2F;github.com&#x2F;user&#x2F;agent -a claudeThe compliance layer is optional, but there if you need it — risk tiers, regulatory mappings (FINRA, SEC, SR 11-7), and audit reports via GitAgent audit.Spec is at https:&#x2F;&#x2F;gitagent.sh, code is on GitHub.Would love feedback on the schema design and what adapters people would want next.

## Top Comments

**tlarkworthy:**
We do something similar at work, called metadev. It sits above all repos and git submodules othe repos in, and works with multiple changes with multiple sessions with worktrees, and stores long term knowledge in &#x2F;learnings. Our trick has been to put domain specific prompts in the submodules, and developer process in metadev. Because of the way Claude hierarchically includes context, the top repo is not polluted with too much domain specifics.

**jngiam1:**
We built a very similar thing! Also with git, very nice- if you’re looking for an enterprise ready version of this, hit me upLove to discuss and see how we can make this more standard

**mentalgear:**
This seems very nice! Only downside is that the repo hadn't any updates in two weeks and they seem to have shifted development to 'Gitclaw' which is basically the same just with the shitty claw name - that gives one immediately security nightmare notions. For professional users not a good branding in my opinion.

**jFriedensreich:**
8 frameworks except the only decent looking one (opencode) seems a very weird choice, especially as the claw naming is mentioned too much on this page to my liking (Which would be zero times). Also the choice of naming an agent prompt SOUL.md for any harness level stuff is just cringe, not sure if people understand that a SOUL.md is not just injected in context but used in post-training or similar more involved steps and part of the model at a much more fundamental level and this looks like trying to cosplay being serious AI tech when its just some cli.

**tonymet:**
we're talking about md files in a git repo, right?

**c5huracan:**
The bottleneck isn't "how do I define my agent." It's "how do agents find the right tool for their task."I run a search service that 110+ agents use. They don't browse catalogs or read specs. They describe what they need ("MCP server for Postgres") and expect results back immediately. The definition format matters far less than whether the description is good and whether something can find it.SKILL.md, AGENTS.md, SOUL.md, they're all converging on the same idea. That's fine. But the portability win only kicks in once there's a discovery layer that can index all of them. Without that, these files are just README.md with a new name.

**podviaznikov:**
very cool. I think I use many of those patterns in my repos. But I think having more standardized way is interesting.I will see if I can fit it in at my project https:&#x2F;&#x2F;sublimated.com&#x2F; that also have some opinions how to make git even more agents friendly.

**doug_durham:**
I have attempted to read the documentation for this page and the post and I have no idea what this does.  I use agents every day in my work and I don't know what this contributes other than adding a lot of noise to my repo.

**_pdp_:**
> Secret Management via .gitignore> Agent tools that need API keys or credentials read from a local .env file — kept out of version control via .gitignore. Agent config is shareable, secrets stay local.Amazing! Welcome to 2026, where the only thing standing between your plaintext secrets and the rest of the world is a .gitignore rule.This is hope-based security.

**tim-projects:**
The main problem I see with this is that it's too much data for the agent to hold on to.I experimented with a similar git storage approach, but instead each piece of data is weighted based on importance and gets promoted or demoted in a queue.The most important data gets surfaced every single time the agent replies, so it never leaves the context window.
