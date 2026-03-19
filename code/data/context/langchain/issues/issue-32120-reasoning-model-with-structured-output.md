# Reasoning model with structured output

**Issue #32120** | State: open | Created: 2025-07-19 | Updated: 2026-03-13
**Author:** wangsiyu666
**Labels:** help wanted, bug, investigate, integration, openai, external

### Checked other resources

- [x] This is a bug, not a usage question. For questions, please use the LangChain Forum (https://forum.langchain.com/).
- [x] I added a clear and detailed title that summarizes the issue.
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I included a self-contained, minimal example that demonstrates the issue INCLUDING all the relevant imports. The code run AS IS to reproduce the issue.

### Example Code

```python
def get_ChatOpenAI(
        model=settings.MODEL_NAME,
        base_url=settings.BASE_URL,
        api_key=settings.API_KEY
):
    llm = BaseChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
    return llm
class Section(BaseModel):
    name: dict = Field(
        description="Name of the analyzed corporate strategic focus e.g.: {'战略点名称': '智能流程自动化'}"
    )
    information: dict = Field(
        description="description of the analyzed corporate strategic focus e.g.: {'战略点说明': '在金融或医疗领域，通过大数据风控模'}"
    )

class AnalysisResult(BaseModel):

    result: List[Section] = Field(
        description="All of Name and description and all plan of the analyzed corporate strategic focus"
    )
analysis_chain = system_prompt | get_ChatOpenAI().with_structured_output(AnalysisResult)
result = analysis_chain.invoke()
```

### Error Message and Stack Trace (if applicable)

```shell
File "E:\大模型\PyCharm 2023.1.2\plugins\python\helpers\pydev\pydevd.py", line 1496, in _exec
    pydev_imports.execfile(file, globals, locals)  # execute the script
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\大模型\PyCharm 2023.1.2\plugins\python\helpers\pydev\_pydev_imps\_pydev_execfile.py", line 18, in execfile
    exec(compile(contents+"\n", file, 'exec'), glob, loc)
  File "E:\strategy_analysis\analysis_graph\analysis_node.py", line 267, in 
    result = asyncio.run(graph.ainvoke(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\asyncio\base_events.py", line 691, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\pregel\__init__.py", line 2920, in ainvoke
    async for chunk in self.astream(
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\pregel\__init__.py", line 2768, in astream
    async for _ in runner.atick(
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\pregel\runner.py", line 401, in atick
    _panic_or_proceed(
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\pregel\runner.py", line 511, in _panic_or_proceed
    raise exc
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\pregel\retry.py", line 137, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\utils\runnable.py", line 672, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langgraph\utils\runnable.py", line 440, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\strategy_analysis\analysis_graph\analysis_node.py", line 159, in OverAllAnalysis
    result = await analysis_chain.ainvoke(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\runnables\base.py", line 3088, in ainvoke
    input_ = await coro_with_context(part(), context, create_task=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\output_parsers\base.py", line 219, in ainvoke
    return await self._acall_with_config(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\runnables\base.py", line 1990, in _acall_with_config
    output: Output = await coro_with_context(coro, context)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\output_parsers\base.py", line 280, in aparse_result
    return await run_in_executor(None, self.parse_result, result, partial=partial)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\runnables\config.py", line 616, in run_in_executor
    return await asyncio.get_running_loop().run_in_executor(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\concurrent\futures\thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\runnables\config.py", line 607, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\output_parsers\openai_tools.py", line 289, in parse_result
    json_results = super().parse_result(result, partial=partial)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\output_parsers\openai_tools.py", line 191, in parse_result
    tool_calls = parse_tool_calls(
                 ^^^^^^^^^^^^^^^^^
  File "C:\ProgramData\anaconda3\envs\hr_analysis\Lib\site-packages\langchain_core\output_parsers\openai_tools.py", line 132, in parse_tool_calls
    raise OutputParserException("\n\n".join(exceptions))
langchain_core.exceptions.OutputParserException: Function AnalysisResult arguments:

{"result": [{"name": {"战略点名称": "促销优化"}, "information": {"战略点说明": "在成熟市场中利用促销手段增加现有产品的吸引力，从而从竞争对手手中争取更多用户。"}}, {"name": {"战略点名称": "渠道优化"}, "information": {"战略点说明": "通过优先考虑高转化率销售渠道或者增强线上/线下分布，提高现有产品的可及性以提升市场份额。"}}, {"name": {"战略点名称": "定价策略调整"}, "information": {"战略点说明": "通过优化和微转型定价策略寻找正确的价格点，既吸引用户又保持利润，压制竞争对手。"}}, {"name": {"战略点名称": "客户保留计划"}, "information": {"战略点说明": "制定奖励和忠诚度计划以提高现有客户的留存率，降低竞争对手夺回份额的机会。"}}, {"name": {"战略点名称": "小众细分定位"}, "information": {"战略点说明": "通过对市场细分挖掘，专注于未被满足的特定用户群体，提高这些群体的市场份额占比。"}}, {"name": {"战略点名称": "快速再定位策略"}, "information": {"战略点说明": "迅速调整产品定位以适应市场变化，反弹回弹能力增强，从而扮演市场领导者角色。"}}, {"name": {"战略点名称": "捆绑销售策略"}, "information": {"战略点说明": "通过将现有产品与畅销产品捆绑，提升销售转化率并吸引未使用本产品的消费者。"}}, {"name": {"战略点名称": "品牌强化活动"}, "information": {"战略点说明": "打造更强的品牌辨识度和用户信任，推动消费者选择自身产品而非竞争对手。"}}, {"name": {"战略点名称": "本地化市场策略"}, "information": {"战略点说明": "根据不同本地市场的需求和偏好，定制化产品推广策略以更好地渗透成熟市场。"}}, {"name": {"战略点名称": "竞争差异化定位"}, "information": {"战略点说明": "挖掘自身产品相比竞争对手的独特优点，利用差异化吸引消费者购买。"}}]
}
are not valid JSON. Received JSONDecodeError Expecting value: line 1 column 1 (char 0)
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE 
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE 
During task with name 'OverAllAnalysis' and id 'a5207214-d084-e8a3-a07a-2c31bf4dddac'
python-BaseException
```

### Description

How to solve the error of using reasoning model with inferred output? deepseek-r1 have 

### System Info

python

## Comments

**langcarl[bot]:**
This issue has been flagged as spam and will be closed. Please tag @ccurme if you feel this was done in error.

**keenborder786:**
First, why are you using `BaseChatOpenAI`, instead of ChatOpenAI. Second, can you share the system prompt, have you given explicity instruction to extract the structured output???

**jmbledsoe:**
FWIW, this is not strictly an OpenAI issue. I am using  Anthropic Claude Opus 4.6 w/ reasoning and encounter the same problem. It seems to me that the output parsers should strip thoughts from the raw LLM response and only parse text.

**keenborder786:**
@jmbledsoe Yeap I was able to replicate this with Deepseek-r1, it adds extra reasoning tokens which raises the parsing error.....

**jmbledsoe:**
I can reliably reproduce the error using this code (thanks @ccurme for collaborating):
```python
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

class MySchema(BaseModel):
    response: str

llm = ChatAnthropic(
    model="claude-opus-4-6",
    output_config={'effort': 'high'},
    thinking={'type': 'adaptive'},
)
structured_llm = llm.with_structured_output(MySchema, method="json_schema")

response = structured_llm.invoke("Hello")
```

**keenborder786:**
Not getting any parsing error using `Deepseek-r1` after #35191.

**keenborder786:**
@ccurme 

Never mind — after running it with DeepSeek R1 multiple times, I still got the parsing error:
```
are not valid JSON. Received JSONDecodeError Expecting value: line 1 column 1 (char 0)
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/OUTPUT_PARSING_FAILURE"
```

For Anthropic Code, PR #35191 fixes this, as we now get the entire text block, thereby avoiding passing an empty string that caused the parsing error in JsonOutputParser in the example above. However, after running DeepSeek R1 about three times, I got the error again, as it concatenated `` tags.

**jackjin1997:**
fixed here https://github.com/langchain-ai/langchain/pull/35530

**jackjin1997:**
Hi, I've already submitted a fix for this issue in PR #35530. Could a maintainer please assign me to this issue so the PR can be reopened? Thanks\!
