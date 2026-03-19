# Show HN: ShapedQL – A SQL engine for multi-stage ranking and RAG

**HN** | Points: 80 | Comments: 23 | Date: 2026-01-27
**Author:** tullie
**HN URL:** https://news.ycombinator.com/item?id=46779922
**Link:** https://playground.shaped.ai

Hi HN,I’m Tullie, founder of Shaped. Previously, I was a researcher at Meta AI, worked on ranking for Instagram Reels, and was a contributor to PyTorch Lightning.We built ShapedQL because we noticed that while retrieval (finding 1,000 items) has been commoditized by vector DBs, ranking (finding the best 10 items) is still an infrastructure problem.To build a decent for you feed or a RAG system with long-term memory, you usually have to put together a vector DB (Pinecone&#x2F;Milvus), a feature store (Redis), an inference service, and thousands of lines of Python to handle business logic and reranking.We built an engine that consolidates this into a single SQL dialect. It compiles declarative queries into high-performance, multi-stage ranking pipelines.HOW IT WORKS:Instead of just SELECT , ShapedQL operates in four stages native to recommendation systems:RETRIEVE: Fetch candidates via Hybrid Search (Keywords + Vectors) or Collaborative Filtering.
FILTER: Apply hard constraints (e.g., "inventory > 0").
SCORE: Rank results using real-time models (e.g., p(click) or p(relevance)).
REORDER: Apply diversity logic so your Agent&#x2F;User doesn’t see 10 nearly identical results.THE SYNTAX: Here is what a RAG query looks like. This replaces about 500 lines of standard Python&#x2F;LangChain code:SELECT item_id, description, priceFROM  -- Retrieval: Hybrid search across multiple indexes

  search_flights("$param.user_prompt", "$param.context"),

  search_hotels("$param.user_prompt", "$param.context")

WHERE  -- Filtering: Hard business constraints

  price <= "$param.budget" AND is_available("$param.dates")

ORDER BY  -- Scoring: Real-time reranking (Personalization + Relevance)

  0.5 * preference_score(user, item) +

  0.3 * relevance_score(item, "$param.user_prompt")

LIMIT 20If you don’t like SQL, you can also use our Python and Typescript SDKs. I’d love to know what you think of the syntax and the abstraction layer!

## Top Comments

**thorax:**
RE: syntax
For casual use, I kinda always liked the whole MATCH&#x2F;AGAINST syntax for old school Innodb, though obviously things have changed a lot since those days. But it felt less like calling embedded functions and more like extending SQL’s grammar.Regarding the rest, it seems like a reasonable approach at first tinker.

**refset:**
Neat examples, and I agree that extending SQL like this has real potential. Another project along very similar lines is https:&#x2F;&#x2F;github.com&#x2F;ryrobes&#x2F;larsql

**jiwidi:**
Great potential! Love the idea

**hrimfaxi:**
If I upload my own data, who exactly is it shared with? I can't find a list of subprocessors and this line in the privacy policy is alarming:> We’ll whenever feasible ask for your consent before using your Personal information for a purpose that isn’t covered in this Privacy Policy.

**mritchie712:**
this is cool, but:> This replaces about 500 lines of standard Pythonisn't really a selling point when an LLM can do it in a few seconds. I think you'd be better off pitching simpler infra and better performance (if that's true).i.e. why should I use this instead of turbopuffer? The answer of "write a little less code" is not compelling.

**pickleballcourt:**
Is there a major difference between pgvector and shapedql?

**JacobiX:**
>> Apply diversity logic so your Agent&#x2F;User doesn’t see 10 nearly identical resultsOn Instagram this is a good thing, but here the example is hotel and flight search, where a more deterministic result is preferable.In the retrieve → filter stage, using predicate pushdown may be more performant: first filter using hard constraints, then apply hybrid search ?

**data_ders:**
I'm a big SQL stan here and I love the concept and if you ever wanna chat about how it might integrate with dbt let me know :)conceptual questions:1) why did you pick SQL?
to increase the Total Addressable Userbase with the thinking that a SQL API means more people can use it than those who know Python or Typescript?2) What isn't or will never be supported by this relational model?
what are the constraints? Clickhouse comes to mind w&#x2F; it's intentionally imposed limitations on JOINs3) databases are historically the stickiest products, but even today SQL dialects are sticky because of how closely tied they are to the query engine. why do you think users will adopt not only a new dialect but a new engine? Especially given that the major DWH vendors have been relentlessly competing to add AI search vector functionality into their products?4) mindsdb comes to mind as something similar that's been in the market for a while but I don't hear it come up often. what makes you different?playground feedback:
1) why are there no examples that:
a) use `JOIN` (that `,` is unhinged syntax imho for an implicit join)
b) don't use `*` (it's cool that there's actual numbers!)2) i kinda get why the search results defaults to a UI, but as a SQL person I first wanted to know what columns exist. I was happy to see "raw table" was available but it took me a while to find it. might be have raw table and UI output visible at the same time with clear instructions on what columns the query requires to populate the UI

**froh42:**
I had a look, so how would I bring my data into it.By exposing my database to services somewhere else in the network. Oh and somewhere else is the US.Fat chance in hell I can anyone in my company look at that or even think about legally applying it with some serious data. (I'm in EU. Yes, a lot of people and companies use US services. Currently it looks like NONE of these can legally do.)It looks interesting, but it needs a on premise solution.
