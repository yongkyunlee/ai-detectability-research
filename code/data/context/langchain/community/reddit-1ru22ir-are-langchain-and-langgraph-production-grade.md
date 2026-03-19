# Are Langchain and Langgraph production grade ?

**r/LocalLLaMA** | Score: 0 | Comments: 22 | Date: 2026-03-15
**Author:** Jaswanth04
**URL:** https://www.reddit.com/r/LocalLLaMA/comments/1ru22ir/are_langchain_and_langgraph_production_grade/

I am wondering what does the community think about langchain and langgraph. Currently the organisation that I work for uses Langgraph and langchain in production applications for chatbots.   
The problems that I see, is langchain has more contrbutions and unneccesary codes, libraries coming in. Example: we use it only as inference but, pandas is also installed which is completely not necessary for my use case, pdf splitter is also not necessary for me. It has 3 to 4 ways of creating react agents or tool calling agents. This results in larger Docker image. 

We have invested in a different monitoring system and only use langgraph for building the graph and running it in a streaming scenario. 

I was wondering, if I can create a library with only the stuff that I use from langgraph and langchain, I will be better off without extra overhead. 

Even though we build multiagent workflows, I dont think langgraph will truly be useful in that case, given that it comes with Pre built prompts for the create\_react\_agent etc.

Please let me know your views on the same.
