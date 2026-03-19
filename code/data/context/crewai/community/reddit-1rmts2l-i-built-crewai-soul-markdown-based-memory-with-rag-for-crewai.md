# I built crewai-soul: Markdown-based memory with RAG for CrewAI

**r/CrewAIInc** | Score: 5 | Comments: 2 | Date: 2026-03-06
**Author:** the-ai-scientist
**URL:** https://www.reddit.com/r/CrewAIInc/comments/1rmts2l/i_built_crewaisoul_markdownbased_memory_with_rag/

Been frustrated that CrewAI's built-in memory is a black box? I built an alternative. 

  
`crewai-soul` stores your agent's identity and memories in readable markdown files:

    from crewai_soul import SoulMemory
    crew = Crew(
        agents=[...],
        memory=SoulMemory(),
    )
    

**What you get:**

• SOUL.md — Agent identity

• MEMORY.md — Timestamped memory log

• Full RAG + RLM hybrid retrieval (via soul-agent)

• Git-versionable — track how memory evolves

• Managed cloud option (SoulMate) for production

**Why markdown?**

• You can read what your agent remembers

• Edit memories when needed

• Version control with git

• No database required  

I wrote a comparison with CrewAI's built-in Memory here: [https://menonlab-blog-production.up.railway.app/blog/crewai-soul-vs-crewai-memory](https://menonlab-blog-production.up.railway.app/blog/crewai-soul-vs-crewai-memory)

  
`pip install crewai-soul`  

It is built on soul.py ([https://github.com/menonpg/soul.py](https://github.com/menonpg/soul.py)) — the open-source memory library for LLM agents.  
  
• PyPI: [https://pypi.org/project/crewai-soul](https://pypi.org/project/crewai-soul)

• GitHub: [https://github.com/menonpg/crewai-soul](https://github.com/menonpg/crewai-soul)  

What memory features would help your crews?
