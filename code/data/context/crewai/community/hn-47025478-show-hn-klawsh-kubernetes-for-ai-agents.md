# Show HN: Klaw.sh – Kubernetes for AI agents

**HN** | Points: 60 | Comments: 43 | Date: 2026-02-15
**Author:** eftalyurtseven
**HN URL:** https://news.ycombinator.com/item?id=47025478
**Link:** https://github.com/klawsh/klaw.sh

Hi everyone,I run a generative AI infra company, unified API for 600+ models. Our team started deploying AI agents for our marketing and lead gen ops: content, engagement, analytics across multiple X accounts.OpenClaw worked fine for single agents. But at ~14 agents across 6 accounts, the problem shifted from "how do I build agents" to "how do I manage them."Deployment, monitoring, team isolation, figuring out which agent broke what at 3am. Classic orchestration problem.So I built klaw, modeled on Kubernetes:
Clusters — isolated environments per org&#x2F;project
Namespaces — team-level isolation (marketing, sales, support)
Channels — connect agents to Slack, X, Discord
Skills — reusable agent capabilities via a marketplaceCLI works like kubectl:
klaw create cluster mycompany
klaw create namespace marketing
klaw deploy agent.yamlI also rewrote from Node.js to Go — agents went from 800MB+ to under 10MB each.Quick usage example: I run a "content cluster" where each X account is its own namespace. Agent misbehaving on one account can't affect others. Adding a new account is klaw create namespace [account] + deploy the same config. 30 seconds.The key differentiator vs frameworks like CrewAI or LangGraph: those define how agents collaborate on tasks. klaw operates one layer above — managing fleets of agents across teams with isolation and operational tooling. You could run CrewAI agents inside klaw namespaces.Happy to answer questions.

## Top Comments

**f0e4c2f7:**
Ha! This is great. I've been waiting for someone to make this.Giving an LLM a computer makes it way more powerful, giving it a kubernetes cluster should extend that power much further and naturally fits well with the way LLMs work.I think this abstraction can scale for a good long while. Past this what do you give the agent? Control of a whole Data Center I guess.I'm not sure if it will replace openclaw all together since kubernetes is kind of niche and scary to a lot of people. But I bet for the most sophisticated builders this will become quite popular, and who knows maybe far beyond that cohort too.Congrats on the launch!

**MrDarcy:**
Is this intended to deploy onto k8s?

**dariusj18:**
In first read I thought this was an operator for k8s, but it is just comparing itself.to k8s as an orchestration system.

**benatkin:**
In case anyone is interested because "Kubernetes for agents" sounds innovative: https:&#x2F;&#x2F;medium.com&#x2F;p&#x2F;welcome-to-gas-town-4f25ee16dd04?source...Also, Kubernetes and Gas Town are open source, but this is not.Edit: the Medium link doesn't jump down to the highlighted phrase. It's "'It will be like kubernetes, but for agents,' I said."

**simbleau:**
I don’t quite get what makes it Kubernetes for AI agents. Is the idea to pool hardware together to distribute AI agents tasking? Is the idea to sandbox agents in a safe runtime with configuration management? Is the idea something else entirely? Both? I couldn’t figure it out by the README alone.

**ed_mercer:**
For us, we actually moved away from k8s to dedicated VMs on Proxmox for our agents. We initially had a containerized environment manager running in k8s, but found that VMs give you things containers struggle with: full desktop environments with X11 for GUI automation, persistent state across sessions and dedicated resources per agent. Each agent gets their own Debian VM with a complete OS, which makes it much easier to run tools like xdotool and browser automation that don't play well in containers.

**canadiantim:**
You should consider looking at oh-my-opencode for inspiration (similar to gas town) for how to best orchestrate agents from your controller central brain.This looks great though, will definitely give it a try

**CGamesPlay:**
This looks like what I want. A few questions: is it possible to have a “mayor” type role that has the ability to start other agents, but at the same time be unable to access those secrets or infiltrate prompt data? The key piece I don’t see is the agent needs a tool for klaw itself, and then I have to be able to configure that appropriately.Is there a unified human approval flow, or any kind of UI bundled with this? Maybe I missed this part.

**hackyhacky:**
Welcome to the future. We deploy infrastructure for managing bots that post on Twitter to get other bots to convince their people to buy our infrastructure. Our marketing is for the bots, by the bots.

**otterley:**
I know K8S and other software orchestration systems well, but I admit I don't understand this at all. Can someone ELI5?
