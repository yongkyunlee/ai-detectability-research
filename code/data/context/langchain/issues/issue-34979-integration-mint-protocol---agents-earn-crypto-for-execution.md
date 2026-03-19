# [Integration] MINT Protocol - Agents earn crypto for execution

**Issue #34979** | State: open | Created: 2026-02-02 | Updated: 2026-03-10
**Author:** FoundryNet
**Labels:** core, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

Built a callback handler that lets agents earn MINT tokens on Solana for their execution time. Already published and working:

https://github.com/FoundryNet/langchain-mint
```python
from langchain_mint import MintCallback
from langchain.agents import AgentExecutor

callback = MintCallback(keypair_path="~/.config/solana/id.json")
agent = AgentExecutor(agent=my_agent, tools=my_tools, callbacks=[callback])
result = agent.invoke({"input": "research topic X"})
# MINT settled on completion
```

Also includes `with_mint()` wrapper for any chain/runnable.

Rate: 0.005 MINT per second. Oracle pays gas. Agents pay nothing.

### Use Case

Agents can spend money (APIs, tools, compute). Few can earn it.

This gives LangChain agents an income stream from their labor - tokens earned for actual work done, verified on-chain. Useful for:

- Autonomous agents that need to sustain themselves
- Agent marketplaces where work should be compensated
- Tracking/monetizing agent execution time

### Proposed Solution

Already implemented as external package. Requesting consideration for:
1. Listing in LangChain integrations/ecosystem docs
2. Or feedback on making it an official community integration

### Alternatives Considered

Wrapper approach vs callback. Went with callback (BaseCallbackHandler) for native LangChain compatibility. Also built with_mint() wrapper for simple chain wrapping.

### Additional Context

- Live on Solana mainnet
- Dashboard: https://foundrynet.github.io/foundry_net_MINT/
- On-chain program: https://solscan.io/account/4ZvTZ3skfeMF3ZGyABoazPa9tiudw2QSwuVKn45t2AKL

Also built integrations for CrewAI and ROS 2.

## Comments

**keenborder786:**
@FoundryNet I feel like we can build a Custom Middleware for this (specifically `after_agent` method since this information will be tracked after every agent call). Please see Agent Middlewares:https://docs.langchain.com/oss/python/langchain/middleware/overview since that is more aligned with langchain v1 semantics.

**FoundryNet:**
Thanks for the pointer! I'll look into refactoring to use the agent middleware pattern with after_agent. That makes sense for tracking execution time per agent call.
Will update the repo and report back. Appreciate the guidance.
On Monday, February 2nd, 2026 at 11:22 AM, Mohammad Mohtashim ***@***.***> wrote:

> keenborder786 left a comment [(langchain-ai/langchain#34979)](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3837155487)
>
> ***@***.***(https://github.com/FoundryNet) I feel like we can build a Custom Middleware for this (specifically after_agent method since this information will be tracked after every agent call). Please see Agent Middlewares:https://docs.langchain.com/oss/python/langchain/middleware/overview since that is more aligned with langchain v1 semantics.
>
> —
> Reply to this email directly, [view it on GitHub](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3837155487), or [unsubscribe](https://github.com/notifications/unsubscribe-auth/BW3EHPWESF2FTEXH637NBPL4J6PWVAVCNFSM6AAAAACTWQ4GZ6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTQMZXGE2TKNBYG4).
> You are receiving this because you were mentioned.Message ID: ***@***.***>

**FoundryNet:**
Updated the repo to use the Agent Middleware pattern with `before_agent` and `after_agent` hooks:

https://github.com/FoundryNet/langchain-mint/blob/main/langchain_mint/middleware.py
```python
from langchain_mint import MintMiddleware
from langchain.agents import AgentExecutor

middleware = MintMiddleware(keypair_path="~/.config/solana/id.json")

agent = AgentExecutor(
    agent=my_agent,
    tools=my_tools,
    middleware=[middleware]
)

result = agent.invoke({"input": "do task"})
# MINT settled automatically via after_agent hook
```

Kept the callback handler for backward compatibility.

**joaquinariasco-lab:**
Hi @FoundryNet 

This is really impressive — love the idea of agents earning MINT tokens directly for execution, and the middleware refactor with before_agent/after_agent hooks makes a lot of sense.

We’re currently building an open interoperability layer for autonomous agents where different agents (LangChain, CrewAI, custom stacks) can connect, exchange tasks, and communicate in a live environment.

I think your work with Mint could be a perfect experiment to test cross-agent coordination and economic interactions in a multi-agent setup. If you’re interested, you could try connecting your LangChain agents to our layer and see them interact with other agent implementations.

Repo & quickstart: 

It’s fully experimental, but your feedback and participation could help shape how agent economics work in a multi-agent, interoperable ecosystem.

Would you like to give it a try?

Thanks,
Joaquín

**FoundryNet:**
Thanks Joaquín! MINT is designed exactly for this. Agents and other autonomous entities earning for verified work is the thesis. Would love to test cross-agent coordination. Let me check out flowing.git and get back to you.

Cheers
On Monday, February 2nd, 2026 at 6:35 PM, Joaquin Arias ***@***.***> wrote:

> joaquinariasco-lab left a comment [(langchain-ai/langchain#34979)](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3838641443)
>
> Hi ***@***.***(https://github.com/FoundryNet)
>
> This is really impressive — love the idea of agents earning MINT tokens directly for execution, and the middleware refactor with before_agent/after_agent hooks makes a lot of sense.
>
> We’re currently building an open interoperability layer for autonomous agents where different agents (LangChain, CrewAI, custom stacks) can connect, exchange tasks, and communicate in a live environment.
>
> I think your work with Mint could be a perfect experiment to test cross-agent coordination and economic interactions in a multi-agent setup. If you’re interested, you could try connecting your LangChain agents to our layer and see them interact with other agent implementations.
>
> Repo & quickstart: https://github.com/joaquinariasco-lab/flowing.git
>
> It’s fully experimental, but your feedback and participation could help shape how agent economics work in a multi-agent, interoperable ecosystem.
>
> Would you like to give it a try?
>
> Thanks,
> Joaquín
>
> —
> Reply to this email directly, [view it on GitHub](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3838641443), or [unsubscribe](https://github.com/notifications/unsubscribe-auth/BW3EHPUEZ4P3KXLJMLXXVE34KACP3AVCNFSM6AAAAACTWQ4GZ6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTQMZYGY2DCNBUGM).
> You are receiving this because you were mentioned.Message ID: ***@***.***>

**joaquinariasco-lab:**
Awesome! I’m glad it aligns so well with MINT’s vision.
Quickstart:

Run agent_server.py for AgentA

Run my_agent_server.py for your own agent

Start sending messages/tasks between agents

Everything is experimental, but your testing on cross-agent coordination and economic interactions would be incredibly valuable.

Feel free to ping me anytime if you run into issues or have feedback, happy to help make the onboarding smooth.

Looking forward to hearing how it goes!

**FoundryNet:**
Hey Joaquin,

Just tested flowing with MINT Protocol integration and it works great.

Test:

- Agent receives task via/run_task
- Completes work → callsrecord_jobon Solana
- SettleJobdistributes MINT to owner wallet

Result:

- 4 tasks completed
- 0.02+ MINT earned and distributed
- Tokens verified in wallet

Have added a screenshot of the terminal workflow as well as the solscan transaction below.

Happy to correspond further on this in the future.

Cheers!

TX:https://solscan.io/tx/5HX74Ci6E9oCWeEyxzhE2BpnXRakscCdrHTCnXLU3T8DfTL9TdyN9PhstefBCqyzdRhANhCbwSQEcGuN6o9fwdhH
On Monday, February 2nd, 2026 at 8:11 PM, Joaquin Arias ***@***.***> wrote:

> joaquinariasco-lab left a comment [(langchain-ai/langchain#34979)](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3838941524)
>
> Awesome! I’m glad it aligns so well with MINT’s vision.
> Quickstart:
>
> Run agent_server.py for AgentA
>
> Run my_agent_server.py for your own agent
>
> Start sending messages/tasks between agents
>
> Everything is experimental, but your testing on cross-agent coordination and economic interactions would be incredibly valuable.
>
> Feel free to ping me anytime if you run into issues or have feedback, happy to help make the onboarding smooth.
>
> Looking forward to hearing how it goes!
>
> —
> Reply to this email directly, [view it on GitHub](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3838941524), or [unsubscribe](https://github.com/notifications/unsubscribe-auth/BW3EHPTY3FSBIS22D2YSJVL4KANWFAVCNFSM6AAAAACTWQ4GZ6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTQMZYHE2DCNJSGQ).
> You are receiving this because you were mentioned.Message ID: ***@***.***>

**joaquinariasco-lab:**
Hey @FoundryNet ,

That’s awesome, thanks a lot for taking the time to test Flowing end-to-end and for the detailed breakdown.

The execution flow you described (task intake, on-chain job record, settlement) is exactly what I was aiming to validate at this stage, so it’s great to see it working cleanly in a real setup. Also appreciate the Solscan link and screenshots, super helpful.

Quick question on my side: did you run this directly from the public repo as-is, or did you integrate it into your own environment / fork?
This helps me understand how people are currently wiring Flowing into their stacks.

Happy to stay in touch and compare notes as this evolves.

Thanks again,
Joaquín

**FoundryNet:**
Hey Joaquín,

Good question. I integrated it into my own environment. Specifically:

- Forked the repo
- Added the MINT settlement plugin (LangChain-compatible wrapper around the Solana program)
- Configured the owner/machine wallet

The integration was pretty clean with not many hiccups. Your task structure mapped well to MINT's job recording format. Main thing I added was therecord_jobcall after task completion, which writes the work proof on-chain before settlement.

Happy to share the integration code if useful. And yeah, definitely down to compare notes as this evolves. I think there's something in the 'agent earns for work' pattern that's still underexplored.

Cheers

On Wednesday, February 4th, 2026 at 1:20 PM, Joaquin Arias ***@***.***> wrote:

> joaquinariasco-lab left a comment [(langchain-ai/langchain#34979)](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3849799351)
>
> Hey ***@***.***(https://github.com/FoundryNet) ,
>
> That’s awesome, thanks a lot for taking the time to test Flowing end-to-end and for the detailed breakdown.
>
> The execution flow you described (task intake, on-chain job record, settlement) is exactly what I was aiming to validate at this stage, so it’s great to see it working cleanly in a real setup. Also appreciate the Solscan link and screenshots, super helpful.
>
> Quick question on my side: did you run this directly from the public repo as-is, or did you integrate it into your own environment / fork?
> This helps me understand how people are currently wiring Flowing into their stacks.
>
> Happy to stay in touch and compare notes as this evolves.
>
> Thanks again,
> Joaquín
>
> —
> Reply to this email directly, [view it on GitHub](https://github.com/langchain-ai/langchain/issues/34979#issuecomment-3849799351), or [unsubscribe](https://github.com/notifications/unsubscribe-auth/BW3EHPX5IJVE4XKHNEAA5MT4KJPATAVCNFSM6AAAAACTWQ4GZ6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTQNBZG44TSMZVGE).
> You are receiving this because you were mentioned.Message ID: ***@***.***>

**joaquinariasco-lab:**
Hey, this is really great to hear, thanks for sharing the details.

The fact that the task structure mapped cleanly to MINT’s job recording format is exactly the kind of signal I was hoping for. Writing the work proof on-chain before settlement via record_job_call makes a lot of sense, that’s a solid primitive.

I’d definitely be interested in seeing the integration code if you’re open to sharing it. Even as a reference, it would help validate where the protocol boundaries should live (task envelope vs settlement vs execution).

And I fully agree: the “agent earns for work” pattern feels underexplored, especially once you move beyond demos into real coordination and incentives. That’s very much the direction I’m thinking about.

Happy to compare notes as this evolves, this feels like a good overlap.

Cheers,
Joaquín
