# Same Chat App, 4 Frameworks: Pydantic AI vs. LangChain vs. LangGraph vs. CrewAI

**HN** | Points: 1 | Comments: 1 | Date: 2026-03-13
**Author:** kacper-vstorm
**HN URL:** https://news.ycombinator.com/item?id=47361387
**Link:** https://oss.vstorm.co/blog/same-chat-app-4-frameworks/

## Top Comments

**kacper-vstorm:**
Everyone has opinions about AI frameworks. Few people show code.We maintain full-stack-ai-agent-template — a production template for AI&#x2F;LLM applications with FastAPI, Next.js, and 75+ configuration options. One of those options is the AI framework. You pick from Pydantic AI, LangChain, LangGraph, or CrewAI during setup, and the template generates the exact same chat application with the exact same API, database schema, WebSocket streaming, and frontend. Only the AI layer differs.This gave us a unique opportunity: a controlled comparison. Same functionality, same tests, same deployment — four implementations.
