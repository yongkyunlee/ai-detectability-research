# Make Redis Vector database operations Asynchronous

**Issue #5234** | State: closed | Created: 2023-05-25 | Updated: 2026-03-14
**Author:** Octforce

### Feature request

There are other vector database that support the use of async in Langchain, adding Redis to those list would be better for programmers who use asynchronous programming in python. I believe with package like aioredis, this should be easily achievable.

### Motivation

The motivation to to be able to support python async programmers with this feature and also to boost performance when querying from the vector store and inserting data into the vector store.

### Your contribution

I can contribute by opening a PR or by testing the code once it is done.

## Comments

**Octforce:**
cc: @tylerhutcherson

**jbkoh:**
https://github.com/hwchase17/langchain/pull/2849

**dosubot[bot]:**
Hi, @Octforce! I'm Dosu, and I'm helping the LangChain team manage their backlog. I wanted to let you know that we are marking this issue as stale. 

Based on my understanding, you opened this issue requesting to make Redis Vector database operations asynchronous to support Python async programmers and improve performance. You mentioned that you are willing to contribute by opening a PR or testing the code once it is implemented. There has been some activity on the issue, with @tylerhutcherson being mentioned and jbkoh sharing a link to a related pull request. You also reacted with a thumbs up to the pull request, indicating that the resolution is satisfactory.

Before we close this issue, we wanted to check with you if it is still relevant to the latest version of the LangChain repository. If it is, please let us know by commenting on the issue. Otherwise, feel free to close the issue yourself or it will be automatically closed in 7 days.

Thank you for your contribution and support!
