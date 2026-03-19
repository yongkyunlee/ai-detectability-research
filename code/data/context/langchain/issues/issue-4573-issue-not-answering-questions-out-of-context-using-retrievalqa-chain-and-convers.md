# Issue: Not answering questions out of context using RetrievalQA Chain and ConversationalChatAgent

**Issue #4573** | State: closed | Created: 2023-05-12 | Updated: 2026-03-11
**Author:** pelyhe

### Issue you'd like to raise.

Hi!

I implemented a chatbot with gpt-4 and a docx file which is provided as context. If I ask questions according to this context, it is returning relevant answers, but if I want to ask a question which is out of this context, it responses 'Based on the provided context I cannot answer this question' or something like that.
How can I implement it in such a way, where it uses the context for every question, but if it cant find relevant answer for it in the context provided, it should take a look in its own language model.

My AgentExecutor instance looks like this:

```
    def _create_chat_agent(self):

        self.llm = OpenAI(temperature=0, model_name="gpt-4", top_p=0.2, presence_penalty=0.4, frequency_penalty=0.2)
        
        # Data Ingestion
        word_loader = DirectoryLoader(DOCUMENTS_DIRECTORY, glob="*.docx")
        documents = []
        documents.extend(word_loader.load())
        # Chunk and Embeddings
        text_splitter = CharacterTextSplitter(chunk_size=768, chunk_overlap=200)
        documents = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Initialise Langchain - QA chain
        qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=vectorstore.as_retriever())

        tools = [
            Tool(
                name="...",
                func=qa.run,
                description="..."
            ),
        ]

        system_msg = "You are a helpful assistant."

        agent = ConversationalChatAgent.from_llm_and_tools(
            llm=self.llm,
            tools=tools,
            system_message=system_msg
        )

        self.chat_agent = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, verbose=True, memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        )
```

### Suggestion:

_No response_

## Comments

**praneetreddy017:**
Could you show me your prompt please?

**pelyhe:**
I call the executor like this: `response = self.chat_agent.run(input=prompt)`. My prompt was 'Say something about Eliza Douglas'.

**praneetreddy017:**
Could you look at the below example and maybe change the LLM initialization portion like in the bottom half of the image and get back to me

![image](https://github.com/hwchase17/langchain/assets/116742376/ef9853f8-e83f-418f-8612-2c22afa17265)

In the image, my data is actually clinical note taken by a doc
I'm asking an irrelevant question and it returns "I don't know" and I am thinking this is because of the way Langchain constructs the final query.

We can modify the query using a custom prompt template to suit our needs and as you can see, we get some answer from the LLM where it constructs a response from its parametric knowledge.
Can you have a look at my example in the image and make those changes and get back to me

**praneetreddy017:**
Include In[7] and In[8] from my code after the line where you initialize the vector store
So it should be something like this:


```
from langchain.prompts import PromptTemplate
.......
.......
vectorstore = FAISS.from_documents(documents, embeddings)

prompt_template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, please think rationally and answer from your own knowledge base 

{context}

Question: {question}
"""
PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

chain_type_kwargs = {"prompt": PROMPT}
qa = RetrievalQA.from_chain_type(llm=OpenAI(), 
                                 chain_type="stuff", 
                                 retriever=vectordb.as_retriever(), 
                                 chain_type_kwargs=chain_type_kwargs)
```

**pelyhe:**
First of all, thank you for being so helpful! 
Unfortunately, the response for this looks like this: 'I apologize for the confusion. There is no information about Eliza Douglas in the context of this conversation.'

**pelyhe:**
![image](https://github.com/hwchase17/langchain/assets/75569619/e3ded06f-520d-4bee-9a2d-2bb149a3df97)
As you can see here, it always want to use the document tool, even if the prompt is not fitting the tool's description.
(I asked it to say something about fifa here, which is irrelevant according to the context)

**praneetreddy017:**
Can you share your code with me. I'm curious and wanna work on this on my own end.

**pelyhe:**
Sure, thank you for your help!

```
from config.db import get_db
from langchain.memory import ConversationBufferMemory
from langchain import PromptTemplate
from langchain.agents import ConversationalChatAgent, Tool, AgentExecutor
from fastapi import HTTPException
from bson import ObjectId
import pickle
import os
import datetime
import logging
from controllers.user_controller import UserController
from langchain.llms import OpenAI
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

DOCUMENTS_DIRECTORY = 'data'

db = get_db()
userModel = db['users']

# THE MODEL WHICH USES GENERAL GPT KNOWLEDGE, BUT DONT ALWAYS RESPONSE WITH THE RIGHT ANSWER

class ChatController(object):
    def __init__(self):
        self._create_chat_agent()

    def _create_chat_agent(self):

        self.llm = OpenAI(temperature=0, model_name="gpt-4", top_p=0.2, presence_penalty=0.4, frequency_penalty=0.2)
        
        # Data Ingestion
        word_loader = DirectoryLoader(DOCUMENTS_DIRECTORY, glob="*.docx")
        documents = []
        documents.extend(word_loader.load())
        # Chunk and Embeddings
        text_splitter = CharacterTextSplitter(chunk_size=768, chunk_overlap=200)
        documents = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(documents, embeddings)

        prompt_template = """Use the following pieces of context to answer the question at the end.
        If you don't know the answer, please think rationally answer from your own knowledge base
        
        {context}
        
        Question: {question}
        """

        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        chain_type_kwargs = {"prompt": PROMPT}
        # Initialise Langchain - QA chain
        qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=vectorstore.as_retriever(), chain_type_kwargs=chain_type_kwargs)

        tools = [
            Tool(
                name="Document tool",
                func=qa.run,
                description="useful for when you need to answer questions about artworks."
            ),
        ]

        system_msg = "You are a helpful assistant."

        agent = ConversationalChatAgent.from_llm_and_tools(
            llm=self.llm,
            tools=tools,
            system_message=system_msg
        )

        self.chat_agent = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, verbose=True, memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        )

    def askAI(self, prompt: str, id: str):
        try:
            objId = ObjectId(id)
        except:
            raise HTTPException(status_code=400, detail="Not valid id.")

        # create a conversation memory and save it if it not exists 
        if not os.path.isfile('conv_memory/'+id+'.pickle'):
            mem = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            with open('conv_memory/' + id + '.pickle', 'wb') as handle:
                pickle.dump(mem, handle, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            # load the memory according to the user id
            with open('conv_memory/'+id+'.pickle', 'rb') as handle:
                mem = pickle.load(handle)

        self.chat_agent.memory = mem

        # for could not parse LLM output
        try:
            response = self.chat_agent.run(input=prompt)
        except ValueError as e:
            response = str(e)
            if not response.startswith("Could not parse LLM output: `"):
                print(e)
                raise e
            response = response.removeprefix(
                "Could not parse LLM output: `").removesuffix("`")

        # save memory after response
        with open('conv_memory/' + id + '.pickle', 'wb') as handle:
            pickle.dump(mem, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return {"answer": response}

```

**praneetreddy017:**
I made some changes and removed whatever I wasn't too sure about (like the db, mem pickle and http stuff)
Changed the db to chromadb too because that is what I was using on my end. 
Key thing seems to be the changes I made to the prompt
So if something irrelevant is passed to the model as a question, the observation it made was "The context does not seem relevant to 'your random topic name here`"

So I changed the prompt to accommodate that and give us the result we desire 

```
from langchain.memory import ConversationBufferMemory
from langchain import PromptTemplate
from langchain.agents import ConversationalChatAgent, Tool, AgentExecutor
import pickle
import os
import datetime
import logging
# from controllers.user_controller import UserController
from langchain.llms import OpenAI
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
# from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma



# THE MODEL WHICH USES GENERAL GPT KNOWLEDGE, BUT DONT ALWAYS RESPONSE WITH THE RIGHT ANSWER

class ChatController(object):
    def __init__(self):
        self._create_chat_agent()

    def _create_chat_agent(self):

        self.llm = OpenAI(temperature=0, top_p=0.2, presence_penalty=0.4, frequency_penalty=0.2)
        embeddings = OpenAIEmbeddings()
        persist_directory = 'myvectordb'
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function = embeddings)


        prompt_template = """If the context is not relevant, 
        please answer the question by using your own knowledge about the topic
        
        {context}
        
        Question: {question}
        """

        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        chain_type_kwargs = {"prompt": PROMPT}
        # Initialise Langchain - QA chain
        qa = RetrievalQA.from_chain_type(llm=self.llm, 
                                         chain_type="stuff", 
                                         retriever=vectorstore.as_retriever(), 
                                         chain_type_kwargs=chain_type_kwargs)

        tools = [
            Tool(
                name="Document tool",
                func=qa.run,
                description="useful for when you need to answer questions."
            ),
        ]

        system_msg = "You are a helpful assistant."

        agent = ConversationalChatAgent.from_llm_and_tools(
            llm=self.llm,
            tools=tools,
            system_message=system_msg
        )

        self.chat_agent = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, verbose=True, memory=ConversationBufferMemory(memory_key="chat_history", 
                                                                                    return_messages=True)
        )

    def askAI(self, prompt: str):
#         try:
#             objId = ObjectId(id)
#         except:
#             raise HTTPException(status_code=400, detail="Not valid id.")

#         # create a conversation memory and save it if it not exists 
#         if not os.path.isfile('conv_memory/'+id+'.pickle'):
#             mem = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
#             with open('conv_memory/' + id + '.pickle', 'wb') as handle:
#                 pickle.dump(mem, handle, protocol=pickle.HIGHEST_PROTOCOL)
#         else:
#             # load the memory according to the user id
#             with open('conv_memory/'+id+'.pickle', 'rb') as handle:
#                 mem = pickle.load(handle)

#         self.chat_agent.memory = mem

        # for could not parse LLM output
        try:
            response = self.chat_agent.run(input=prompt)
        except ValueError as e:
            response = str(e)
#             if not response.startswith("Could not parse LLM output: `"):
#                 print(e)
#                 raise e
#             response = response.removeprefix(
#                 "Could not parse LLM output: `").removesuffix("`")

#         # save memory after response
#         with open('conv_memory/' + id + '.pickle', 'wb') as handle:
#             pickle.dump(mem, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return {"answer": response}
        

x = ChatController()
x.askAI("fifa")
```

![image](https://github.com/hwchase17/langchain/assets/116742376/28ecbdaa-fafc-4a35-9cd5-67b030a7e6f1)

**praneetreddy017:**
Please read this and let me know if it works @pelyhe
