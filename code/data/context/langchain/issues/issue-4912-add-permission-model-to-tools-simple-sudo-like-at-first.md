# Add permission model to tools (simple sudo like at first)

**Issue #4912** | State: closed | Created: 2023-05-18 | Updated: 2026-03-17
**Author:** thompsonson

### Feature request

# Example

I have a tool that has access to my email. This tool is used by a long running agent. I'd like the tool to have long standing Read permissions but only have short lived Write permissions. 

Like Githubs sudo permission, I'd like a message sent to a designated device, email, or similar, asking for authorization. 

# Reality

Some of these actions maybe outside the design scope of LangChain. However, my mind goes towards a refining of the _run method within a tool. The _run method could accept an object which is responsible for getting approval or simply returning true. 

As a pattern I think of dependency injection more than callbacks but wonder if that could work or it is just semantic difference. 



### Motivation

Motivation is simply to secure the use of tools. After regulation of the underlying LLMs I think this is the next largest risk.  

I think it talks to ~~Ben (sorry I forget his surname)~~ EDIT: got the gents name wrong, his name is Simon Wilson ( https://simonwillison.net/2023/May/2/prompt-injection-explained/)  recent concerns and suggestion to have two LLMs, one freely accessible the other privileged and has input sanitized.

There is a lot of value in the thought and pattern, it feels more practical to start with permissions, especially in a "zero trust world".

### Your contribution

Happy to help in multiple ways, time based.

Immediately to discuss and document the risks, threats, and previous solutions.

Immediately to peer review MRs. 

Mid-Longer term (i.e. on the back of a decent to do list) start to code a solution.

## Comments

**dosubot[bot]:**
Hi, @thompsonson! I'm Dosu, and I'm here to help the LangChain team manage their backlog. I wanted to let you know that we are marking this issue as stale. 

From what I understand, you opened this issue as a feature request to add a permission model to tools. You mentioned that you are motivated to secure the use of tools and are willing to contribute to the discussion, documentation, and potentially coding a solution. However, there hasn't been any activity on this issue yet.

Before we close this issue, we wanted to check with you if it is still relevant to the latest version of the LangChain repository. If it is, please let us know by commenting on the issue. Otherwise, feel free to close the issue yourself, or it will be automatically closed in 7 days.

Thank you for your understanding and contribution to the LangChain project! Let us know if you have any further questions or concerns.

**thompsonson:**
Hello Dosu,

Yes, this is still relevant for me. I have two use cases:

1. A personal AI assisstant: I give the AI assistant access to my email (e.g. permissions to read and send email), however I wish to mitigate the risk that it sends emails I do not wish to be sent. This is to avoid simple mistakes in the intent of my query to the AI assistant and the more serious issue of my AI assistant being compromised (directly or jailbroken). If it is the later, yes my email content is compromised, however they are not able to send any emails (further exasberating the indicent).

2. I have some data that is very private, e.g. health records or legal documents, this is stored in a place where the agent can get access to a one time token and read the files. I'd like to be able to authorise the agent to get a temporary access to these documents.

What do you think?

Best wishes,
Matt

**dosubot[bot]:**
@baskaryan Could you please help @thompsonson with this issue? They have indicated that it is still relevant and provided additional context on their use cases. Thank you!

**dosubot[bot]:**
Hi, @thompsonson. I'm Dosu, and I'm here to help the LangChain team manage our backlog. I wanted to let you know that we are marking this issue as stale. 

From what I understand, this issue is a feature request to add a permission model to tools, allowing for long-standing read permissions and short-lived write permissions. The goal is to secure the use of tools and mitigate risks. You have confirmed that the issue is still relevant and provided additional context on your use cases. Another user has been asked to help with the issue.

Before we proceed, we would like to confirm if this issue is still relevant to the latest version of the LangChain repository. If it is, please let us know by commenting on this issue. Otherwise, feel free to close the issue yourself, or the issue will be automatically closed in 7 days.

Thank you for your understanding and cooperation. If you have any further questions or concerns, please let me know.

Dosu

**thompsonson:**
I'm not looking to re-open this specific issue, however Ive had time to look into the work I believe is required for me to start on.

here is my initial 1Pager: https://docs.google.com/document/d/1PTPDrWyEwogZh_qO_6d6ZUPM2t82Fzj9c5D_UZZHL7s/edit?usp=sharing

If feedback/review is possible please do share 😁

**uchibeke:**
This issue is still very much relevant — the permission model for tools problem has only gotten more urgent as LangChain agents get deployed in production with access to email, databases, and external APIs.

For anyone landing here: a LangChain integration for this exact pattern now exists.

**[APort Agent Guardrails](https://github.com/aporthq/aport-agent-guardrails)** implements a pre-action authorization layer for LangChain tools. The integration lives at [`packages/langchain/`](https://github.com/aporthq/aport-agent-guardrails/tree/main/packages/langchain) in the repo. It wraps LangChain tool calls with a `before_tool_call` hook that evaluates a YAML policy before any tool executes — the pattern @thompsonson described (long-lived read permissions, short-lived write permissions, out-of-band approval for sensitive operations) is exactly what OAP policy supports.

The underlying spec — the [Open Agent Protocol (OAP)](https://github.com/aporthq/aport-spec) — is a DOI-archived open standard ([doi.org/10.5281/zenodo.18901596](https://doi.org/10.5281/zenodo.18901596)), so this isn't a proprietary lock-in: it's a portable permission model that works the same way across LangChain, CrewAI, n8n, Claude Code, Cursor, and OpenClaw.

The key design decision that makes this different from prompt-level "ask before acting" instructions: enforcement runs at the runtime/framework level, not in the model response. Prompt injection can instruct an agent to skip a prompt-layer confirmation step. A `before_tool_call` hook at the framework level cannot be bypassed by model output — the platform calls it for every tool invocation regardless of what the model says.

We'd be happy to submit a PR adding the LangChain integration to LangChain's contrib packages. The implementation is already built and tested — it would just be a matter of packaging it in a way that fits LangChain's contribution guidelines.

Guardrails repo (incl. LangChain package): https://github.com/aporthq/aport-agent-guardrails  
OAP spec: https://github.com/aporthq/aport-spec  
DOI: https://doi.org/10.5281/zenodo.18901596

**uchibeke:**
Hi all, I opened an issue to unify this and allow users pick their own guardrail provider https://github.com/openclaw/openclaw/issues/46441

**maxsnow651-dev:**
Alright thank u for the information

On Mon, Mar 16, 2026, 7:37 PM Uchi Uchibeke ***@***.***>
wrote:

> *uchibeke* left a comment (langchain-ai/langchain#4912)
> 
>
> Hi all, I opened an issue to unify this and allow users pick their own
> guardrail provider openclaw/openclaw#46441
> 
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
