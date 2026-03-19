# langchain-openai 无法读取到 qwen3 think 的过程 希望 支持 qwen3 像 支持 deepseek一样（initChatModel）

**Issue #33672** | State: open | Created: 2025-10-26 | Updated: 2026-03-16
**Author:** CodeXiaoHan
**Labels:** feature request, openai, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Feature Description

langchain-openai   支持 qwen3 像 支持 deepseek 一样（initChatModel）可以获取 qwen3 think 的过程

### Use Case

langchain-openai 无法读取到 qwen3 think 的过程 希望 支持 qwen3 像 支持 deepseek一样（initChatModel）
描述：我在使用 createAgent 的时候发现 使用 chatOpenAI 传入 qwen3 的模型（支持思考模式）后 ，无法 获取到 qwen3的思考过程，尝试了很多都无法实现。
使用 ChatTongyi 无法满足我调用本地服务器上的qwen3模型的，因为它的 baseURL 或 apiURL 不允许修改。 
最重要的一点是：像 qwen3 这种支持思考的模式 ，我在使用 createAgent 的时候，获取不到思考过程，导致不管是 invoke 或 stream  都会等待很长时间才会有内容输出，会让用户以为功能有问题。

### Proposed Solution

_No response_

### Alternatives Considered

尝试过替换为 openAI 官方 SDK 是可以实现 获取 qwen3 的思考过程，但这和 langchain 就没有任何关系了

### Additional Context

_No response_

## Comments

**TmacChenQian:**
也就是说对于qwen_的思考模式目前langchain的ChatOpenAI是没有获取到思考内容的，我看返回的chunk里面没有做任何标记
OpenAI原生的就有标记

**AmazingcatAndrew:**
这个问题本质上是因为qwen调用的是基类ChatOpenAI的方法，ChatOpenAI类中没有针对特定模型（包括qwen）的处理逻辑。而deepseek在 partners/deepseek/ 下有独立的适配类（继承自ChatOpenAI），这个类中有对于思考内容的输出处理逻辑。直接给qwen创建独立的适配类是不符合标准的，因为qwen的参数与返回结构严格遵守 OpenAI 格式（除了可能多出思考字段），只要它是“接口兼容”，就不应新建 partner 包或子类。所以我正在考虑别的方案。我愿意接手这个issue，请给我一周时间处理。
The root of this problem is that Qwen is calling the methods of the base class ChatOpenAI, and the ChatOpenAI class doesn't have specific processing logic for particular models (including Qwen). In contrast, DeepSeek has an independent adapter class (inherited from ChatOpenAI) under partners/deepseek/, which includes processing logic for the output of thinking content. Creating an independent adapter class for Qwen directly doesn't meet the standards, because Qwen's parameters and return structure strictly adhere to the OpenAI format (except for the potential addition of a "thinking" field). As long as it is "interface compatible," a new partner package or subclass should not be created. Therefore, I am considering other solutions. I am willing to take on the issue, please give me 1 week to handle.

**KK5241:**
是不是 qwen3-embedding-4b 使用 OpenAIEmbeddings类一样 也会出现这样的问题，我这边遇到的是模型返回了向量 但是langchain返回的结果全部都是0

**wl92641112:**
我今天改了原代码_create_chat_result的函数，让init_chat_model 函数可以返回 reasoning_content。用from openai import OpenAI 是可以直接返回的，但是用了OpenAI 我就不可以链式调用了

**wl92641112:**
该部分代码是没有合并的吗？我在最新的&nbsp;langchain-openai&nbsp;并未看到该部分代码


。。。
***@***.***



        



         原始邮件
         
       
发件人：AmazingcatAndrew ***@***.***&gt;
发件时间：2025年12月17日 22:49
收件人：langchain-ai/langchain ***@***.***&gt;
抄送：睡觉了吗 ***@***.***&gt;, Manual ***@***.***&gt;
主题：Re: [langchain-ai/langchain] langchain-openai 无法读取到 qwen3 think 的过程 希望 支持 qwen3 像 支持 deepseek一样（initChatModel） (Issue #33672)



AmazingcatAndrew left a comment (langchain-ai/langchain#33672)

各位可以去看看我之前的PR #33836&nbsp;，官方维护者在底下说这个问题已经被 #32982&nbsp;解决

—
Reply to this email directly, view it on GitHub, or unsubscribe.
You are receiving this because you are subscribed to this thread.

**CodeXiaoHan:**
> 该部分代码是没有合并的吗？我在最新的&nbsp;langchain-openai&nbsp;并未看到该部分代码
> 
> 
> 。。。
> ***@***.***
> 
> 
> 
> 
> 
> 
> 
>          原始邮件
> 
> 
> 发件人：AmazingcatAndrew ***@***.***&gt;
> 发件时间：2025年12月17日 22:49
> 收件人：langchain-ai/langchain ***@***.***&gt;
> 抄送：睡觉了吗 ***@***.***&gt;, Manual ***@***.***&gt;
> 主题：Re: [langchain-ai/langchain] langchain-openai 无法读取到 qwen3 think 的过程 希望 支持 qwen3 像 支持 deepseek一样（initChatModel） (Issue [#33672](https://github.com/langchain-ai/langchain/issues/33672))
> 
> 
> 
> AmazingcatAndrew left a comment ([langchain-ai/langchain#33672](https://github.com/langchain-ai/langchain/issues/33672))
> 
> 各位可以去看看我之前的PR [#33836](https://github.com/langchain-ai/langchain/pull/33836)&nbsp;，官方维护者在底下说这个问题已经被 [#32982](https://github.com/langchain-ai/langchain/pull/32982)&nbsp;解决
> 
> —
> Reply to this email directly, view it on GitHub, or unsubscribe.
> You are receiving this because you are subscribed to this thread.

啥时候解决的。没看到，我是自己写了一个实现类来解决这个问题的

**congxiao-wxx:**
same here

**congxiao-wxx:**
这个问题最终langchain官方解决了吗

**friendllcc:**
我今天也遇到了，还没解决吗？看到了这篇帖子：https://www.langchain.cn/t/topic/751
官方回答是认为把reasoning_content返回会比较笨重~额

**friendllcc:**
希望langchain官方快点解决，不要丢弃reasoning_content
