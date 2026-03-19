# ConversationalRetrievalChain + Memory

**Issue #2303** | State: closed | Created: 2023-04-02 | Updated: 2026-03-07
**Author:** da-bu

Hi, 

I'm following the [Chat index examples](https://python.langchain.com/en/latest/modules/chains/index_examples/chat_vector_db.html) and was surprised that the history is not a Memory object but just an array. However, it is possible to pass a memory object to the constructor, if 

1. I also set memory_key to 'chat_history' (default key names are different between ConversationBufferMemory and ConversationalRetrievalChain)
2. I also adjust get_chat_history to pass through the history from the memory, i.e. lambda h : h.

This is what that looks like:

```
memory = ConversationBufferMemory(memory_key='chat_history', return_messages=False)
conv_qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm, 
    retriever=retriever, 
    memory=memory,
    get_chat_history=lambda h : h)
```

Now, my issue is that if I also want to return sources that doesn't work with the memory - i.e. this does not work:
```
memory = ConversationBufferMemory(memory_key='chat_history', return_messages=False)
conv_qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm, 
    retriever=retriever, 
    memory=memory,
    get_chat_history=lambda h : h,
    return_source_documents=True)
```

The error message is "ValueError: One output key expected, got dict_keys(['answer', 'source_documents'])".

Maybe I'm doing something wrong? If not, this seems worth fixing to me - or, more generally, make memory and the ConversationalRetrievalChain more directily compatible?

## Comments

**xyfusion:**
I am having similar issue. Memory with ChatOpenAI works fine for the Conversation chain, but not fully compatible with ConversationalRetrievalChain. Look forward to hearing a working solution on this given retrieval is a common use case in conversation chains.

**malcolmosh:**
A chat_history object consisting of (user, human) string tuples passed to the ConversationalRetrievalChain.from_llm method will automatically be formatted through the [_get_chat_history function](https://github.com/hwchase17/langchain/blob/master/langchain/chains/conversational_retrieval/base.py#L22). In a chatbot, you can simply keep appending inputs and outputs to the chat_history list and use it instead of ConversationBufferMemory. This chat_history list will be nicely formatted in the prompt sent to an LLM. Though I agree that the overall concept of memory should be applicable everywhere and things should be harmonized...

**jordanparker6:**
> A chat_history object consisting of (user, human) string tuples passed to the ConversationalRetrievalChain.from_llm method will automatically be formatted through the [_get_chat_history function](https://github.com/hwchase17/langchain/blob/master/langchain/chains/conversational_retrieval/base.py#L22). In a chatbot, you can simply keep appending inputs and outputs to the chat_history list and use it instead of ConversationBufferMemory. This chat_history list will be nicely formatted in the prompt sent to an LLM. Though I agree that the overall concept of memory should be applicable everywhere and things should be harmonized...

I have been playing around with this today. The `_get_chat_history` function stuffs a provided list of history tuples into the a preliminary query that reforms the input as a new question with the following prompt.

```
CONDENSE_QUESTION_TEMPLATE = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
```

 It then follows the regular retrieval prompt, providing both the context retrieved from the retriver and the summarised question (given the history). This approach to conversational memory broke down pretty quickly when asked questions about past inputs. Taking the history and summarising it in a new question seem to create a mismatch between the new question and the context. For example:

input
```
history = [
    ("What is the date Australia was founded.", "Australia was founded in 1901."),
]

chain({ "question": "What was the last question I asked you.", "chat_history": history }, return_only_outputs=True)
```

logs
```
DEBUG:openai:api_version=None data='{"messages": [{"role": "system", "content": "Use the following pieces of context to answer the users question. \\nIf you don\'t know the answer, just say that you don\'t know, don\'t try to make up an answer.\\n {}"}, {"role": "user", "content": "Can you remind me of the last question I asked you?"}], "model": "gpt-3.5-turbo", "max_tokens": null, "stream": false, "n": 1, "temperature": 0}' message='Post details'

```

This returned `'Your last question was "What are the pieces of context that can be used to answer the user\'s question?"'`

Which is a summary of the QA_Prompt template itself...

Would following the ChatOpenAI API of a list of the raw messages with the history injected avoid this? It is kind of like the windowed conversational memory buffer? The summarisation into a new question may be doing a disservice for answering basic conversational memory as the conversation isn't provided as context...

**ogmios2:**
Definitely issues. Just spent 2 days racking my brain on trying to make a "chain" of Pinecone retrieval, prompt template, chat history... which you'd think that it would be easy and whole purpose of LangChain to have various blocks or pieces of chains work well together. 

It seems that ConversationRetrievalChain does not work with context, history and prompt template at all. It semi works with some, but not as whole.

**ToddKerpelman:**
So I think the issue here is that the `BaseChatMemory` gets all confused when the output it receives contains more then one key, and it doesn't know which one to assign as the answer; it's in this code here:

```        
if self.output_key is None:
            if len(outputs) != 1:
                raise ValueError(f"One output key expected, got {outputs.keys()}")
            output_key = list(outputs.keys())[0]
        else:
```
When you have `return_source_documents=True,` the output has two keys: `answer` and `source_documents`, and that causes this to throw an error.

The workaround  that got this working for me was to specify `answer` as the output key when creating this ConversationBufferMemory object. Then it doesn't have to try to guess at what the output_key is.

```
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True, output_key='answer')
```

**My3VM:**
I too had similar issue, thanks for this response!

**amitmukh:**
I have the similar issue. 
qa=ConversationalRetrievalChain.from_llm(
            llm=llm,
            chain_type = "stuff",
            retriever=index.as_retriever(),
            return_source_documents=True,
            memory =st.session_state.memory
            )
In fact, if I remove the "return_source_documents=True," line then I am getting another issue:
pydantic.error_wrappers.ValidationError: 1 validation error for AIMessage
content
  str type expected (type=type_error.str)

**nickmuchi87:**
I have the same issue as well, has anyone manage to use that chain with memory, a custom prompt and return_source_documents? I was getting errors. I added my prompt template under qa_prompt and got errors.

**jeloooooo:**
@nickmuchi87 please see @ToddKerpelman 's answer, add the output_key='answer' in the ConversationBufferMemory. This worked for me.

```
 memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True, output_key='answer')
```

**nickmuchi87:**
Ye that worked when I did not have a custom prompt but when I tried to include a prompt I got a context error.
