# Human as a Tool in Production 

**Issue #8973** | State: closed | Created: 2023-08-09 | Updated: 2026-03-07
**Author:** Ajaypawar02

### Issue you'd like to raise.

Can we use Human as a tool in product?
def get_input() -> str:
    print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "q":
            break
        contents.append(line)
    return "\n".join(contents)


# You can modify the tool when loading
tools = load_tools(["human", "ddg-search"], llm=math_llm, input_func=get_input)

what to do with input() in get_input() function if we need to use this tool in production?

reference:-https://python.langchain.com/docs/integrations/tools/human_tools

### Suggestion:

_No response_

## Comments

**pprados:**
I suppose using the 'human' tool is difficult on a web server ;-)

**dosubot[bot]:**
Hi, @Ajaypawar02! I'm Dosu, and I'm here to help the LangChain team manage their backlog. I wanted to let you know that we are marking this issue as stale. 

From what I understand, you opened this issue asking for guidance on what to do with the `input()` function in the `get_input()` function. There was a comment from pprados, who humorously mentioned the difficulty of using the "human" tool on a web server. 

Before we close this issue, we wanted to check if it is still relevant to the latest version of the LangChain repository. If it is, please let us know by commenting on the issue. Otherwise, feel free to close the issue yourself, or it will be automatically closed in 7 days. 

Thank you for your contribution to the LangChain repository!

**MariusAure:**
Yeah `input()` is useless in production. I ended up making an API the agent can POST to, a human picks it up and does the thing, agent GETs the result when it's ready. https://needhuman.ai
