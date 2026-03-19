# Chroma is not ephemeral when persisted_directory=None

**Issue #28774** | State: closed | Created: 2024-12-17 | Updated: 2026-03-06
**Author:** realliyifei
**Labels:** bug

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
from langchain.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_openai import OpenAIEmbeddings

def retrieval_gpt_generate(query: str,
                           retrieved_documents: List[Document],
                           ):
    texts = text_splitter.split_documents(retrieved_documents)
    embeddings = OpenAIEmbeddings(openai_api_key=constants.OPENAI_API_KEY, max_retries=1000)
    docsearch = Chroma.from_documents(filter_complex_metadata(texts), embeddings, persist_directory=None)
    
    doc_retriever = docsearch.as_retriever(search_kwargs={"k": 5})
    topk_relevant_passages = doc_retriever.get_relevant_documents(query)
    return topk_relevant_passages

for each new {query, retrieved_documents}:
	topk_relevant_passages  = retrieval_gpt_generate(query, retrieved_documents)
	print(topk_relevant_passages)
```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

The `topk_relevant_passages` includes the one from the previous iteration, that is, it would use the previous retrieved_documents. I am pretty sure the retrieved_documents input is entirely different in each iteration. I checked the intermediate docsearch, it is persisted. But I believe by setting `persist_directory=None`, the RAG should be ephemeral in-memory. 

### System Info

Passage1
Passage2 # Using the source from the previous iteration (it shouldn’t)
Passage3 
...

## Comments

**keenborder786:**
@realliyifei You are absolutely right, between every iteration despite creating a new instance of Chroma, same in-memory storage is being used. I verified by the following:

```python

from typing import List
from langchain.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
def retrieval_gpt_generate(query: str,
                           retrieved_documents: List[Document],
                           ):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(retrieved_documents)
    embeddings = OpenAIEmbeddings(max_retries=1000)
    docsearch = Chroma.from_documents(filter_complex_metadata(texts), embeddings)
    print(len(docsearch.get()['ids']))
    doc_retriever = docsearch.as_retriever(search_kwargs={"k": 1})
    topk_relevant_passages = doc_retriever.get_relevant_documents(query)
    return topk_relevant_passages
docs = [
    [Document(page_content="France's Capital is Paris", metadata={}),
     Document(page_content="France is a country", metadata={}),
     Document(page_content="Germany's Capital is Berlin", metadata={}),
     Document(page_content="Germany is a country", metadata={}),
     Document(page_content="Italy's Capital is Rome", metadata={}),
     Document(page_content="Italy is a country", metadata={})],

    [Document(page_content="Spain's Capital is Madrid", metadata={}),
     Document(page_content="Spain is a country", metadata={}),
     Document(page_content="Japan's Capital is Tokyo", metadata={}),
     Document(page_content="Japan is an island nation", metadata={}),
     Document(page_content="Canada's Capital is Ottawa", metadata={}),
     Document(page_content="Canada is a country", metadata={})],

    [Document(page_content="Brazil's Capital is Brasília", metadata={}),
     Document(page_content="Brazil is a country", metadata={}),
     Document(page_content="India's Capital is New Delhi", metadata={}),
     Document(page_content="India is a country", metadata={}),
     Document(page_content="Australia's Capital is Canberra", metadata={}),
     Document(page_content="Australia is a country", metadata={})],

    [Document(page_content="Russia's Capital is Moscow", metadata={}),
     Document(page_content="Russia is the largest country", metadata={}),
     Document(page_content="Mexico's Capital is Mexico City", metadata={}),
     Document(page_content="Mexico is a country", metadata={}),
     Document(page_content="South Africa's Capital is Pretoria", metadata={}),
     Document(page_content="South Africa is a country", metadata={})],

    [Document(page_content="United Kingdom's Capital is London", metadata={}),
     Document(page_content="United Kingdom is a country", metadata={}),
     Document(page_content="Argentina's Capital is Buenos Aires", metadata={}),
     Document(page_content="Argentina is a country", metadata={}),
     Document(page_content="Egypt's Capital is Cairo", metadata={}),
     Document(page_content="Egypt is a country", metadata={})],

    [Document(page_content="China's Capital is Beijing", metadata={}),
     Document(page_content="China is a country", metadata={}),
     Document(page_content="South Korea's Capital is Seoul", metadata={}),
     Document(page_content="South Korea is a country", metadata={}),
     Document(page_content="Indonesia's Capital is Jakarta", metadata={}),
     Document(page_content="Indonesia is a country", metadata={})]
]
for retrived_docs in docs:
    retrieval_gpt_generate("What is capital of france",retrived_docs)

```

The output for above was as follow:

```bash
6
12
18
24
30
36
```
which shows same document are being persisted across each iteration. My guess is that behind the scenes Chroma keeps using the same memory in the single python process. As you can see when I ran each iteration in a different python process, the number of documents remained 6.


```python

from typing import List
from langchain.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from multiprocessing import Process


def retrieval_gpt_generate(query: str,
                           retrieved_documents: List[Document],
                           ):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(retrieved_documents)
    embeddings = OpenAIEmbeddings(max_retries=1000)
    docsearch = Chroma.from_documents(filter_complex_metadata(texts), embeddings)
    print(len(docsearch.get()['ids']))
    doc_retriever = docsearch.as_retriever(search_kwargs={"k": 1})
    topk_relevant_passages = doc_retriever.get_relevant_documents(query)
    return topk_relevant_passages


docs = [
    [Document(page_content="France's Capital is Paris", metadata={}),
     Document(page_content="France is a country", metadata={}),
     Document(page_content="Germany's Capital is Berlin", metadata={}),
     Document(page_content="Germany is a country", metadata={}),
     Document(page_content="Italy's Capital is Rome", metadata={}),
     Document(page_content="Italy is a country", metadata={})],

    [Document(page_content="Spain's Capital is Madrid", metadata={}),
     Document(page_content="Spain is a country", metadata={}),
     Document(page_content="Japan's Capital is Tokyo", metadata={}),
     Document(page_content="Japan is an island nation", metadata={}),
     Document(page_content="Canada's Capital is Ottawa", metadata={}),
     Document(page_content="Canada is a country", metadata={})],

    [Document(page_content="Brazil's Capital is Brasília", metadata={}),
     Document(page_content="Brazil is a country", metadata={}),
     Document(page_content="India's Capital is New Delhi", metadata={}),
     Document(page_content="India is a country", metadata={}),
     Document(page_content="Australia's Capital is Canberra", metadata={}),
     Document(page_content="Australia is a country", metadata={})],

    [Document(page_content="Russia's Capital is Moscow", metadata={}),
     Document(page_content="Russia is the largest country", metadata={}),
     Document(page_content="Mexico's Capital is Mexico City", metadata={}),
     Document(page_content="Mexico is a country", metadata={}),
     Document(page_content="South Africa's Capital is Pretoria", metadata={}),
     Document(page_content="South Africa is a country", metadata={})],

    [Document(page_content="United Kingdom's Capital is London", metadata={}),
     Document(page_content="United Kingdom is a country", metadata={}),
     Document(page_content="Argentina's Capital is Buenos Aires", metadata={}),
     Document(page_content="Argentina is a country", metadata={}),
     Document(page_content="Egypt's Capital is Cairo", metadata={}),
     Document(page_content="Egypt is a country", metadata={})],

    [Document(page_content="China's Capital is Beijing", metadata={}),
     Document(page_content="China is a country", metadata={}),
     Document(page_content="South Korea's Capital is Seoul", metadata={}),
     Document(page_content="South Korea is a country", metadata={}),
     Document(page_content="Indonesia's Capital is Jakarta", metadata={}),
     Document(page_content="Indonesia is a country", metadata={})]
]


def process_documents(retrieved_docs: List[Document]):
    retrieval_gpt_generate("What is capital of france", retrieved_docs)


if __name__ == '__main__':
    # Create a list to store process objects
    processes = []
    
    for retrived_docs in docs:
        # Create a new process for each set of documents
        p = Process(target=process_documents, args=(retrived_docs,))
        processes.append(p)
        p.start()  # Start the process

    # Wait for all processes to complete
    for p in processes:
        p.join()

```


```bash
6
6
6
6
6
6
```

**realliyifei:**
Thanks for the verification. Is there any quick workaround for the original code? I don't think I would run them in different processes.

**keenborder786:**
Currently No :(

**realliyifei:**
A quick fix is to reset the chromadb instance each time (another workaround may be creating new collections each time via chromadb):

```python
from typing import List
from langchain.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

def retrieval_gpt_generate(query: str,
                           retrieved_documents: List[Document],
                           ):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(retrieved_documents)
    embeddings = OpenAIEmbeddings(max_retries=1000)
    client = chromadb.PersistentClient(settings=chromadb.Settings(allow_reset=True))
    client.reset() # reset the chromadb instance, otherwise the retrieved documents will be cached from previous runs
    docsearch = Chroma.from_documents(filter_complex_metadata(texts), embeddings, client=client)
    print(len(docsearch.get()['ids']))
    doc_retriever = docsearch.as_retriever(search_kwargs={"k": 1})
    topk_relevant_passages = doc_retriever.get_relevant_documents(query)
    return topk_relevant_passages
docs = [
    [Document(page_content="France's Capital is Paris", metadata={}),
     Document(page_content="France is a country", metadata={}),
     Document(page_content="Germany's Capital is Berlin", metadata={}),
     Document(page_content="Germany is a country", metadata={}),
     Document(page_content="Italy's Capital is Rome", metadata={}),
     Document(page_content="Italy is a country", metadata={})],

    [Document(page_content="Spain's Capital is Madrid", metadata={}),
     Document(page_content="Spain is a country", metadata={}),
     Document(page_content="Japan's Capital is Tokyo", metadata={}),
     Document(page_content="Japan is an island nation", metadata={}),
     Document(page_content="Canada's Capital is Ottawa", metadata={}),
     Document(page_content="Canada is a country", metadata={})],

    [Document(page_content="Brazil's Capital is Brasília", metadata={}),
     Document(page_content="Brazil is a country", metadata={}),
     Document(page_content="India's Capital is New Delhi", metadata={}),
     Document(page_content="India is a country", metadata={}),
     Document(page_content="Australia's Capital is Canberra", metadata={}),
     Document(page_content="Australia is a country", metadata={})],

    [Document(page_content="Russia's Capital is Moscow", metadata={}),
     Document(page_content="Russia is the largest country", metadata={}),
     Document(page_content="Mexico's Capital is Mexico City", metadata={}),
     Document(page_content="Mexico is a country", metadata={}),
     Document(page_content="South Africa's Capital is Pretoria", metadata={}),
     Document(page_content="South Africa is a country", metadata={})],

    [Document(page_content="United Kingdom's Capital is London", metadata={}),
     Document(page_content="United Kingdom is a country", metadata={}),
     Document(page_content="Argentina's Capital is Buenos Aires", metadata={}),
     Document(page_content="Argentina is a country", metadata={}),
     Document(page_content="Egypt's Capital is Cairo", metadata={}),
     Document(page_content="Egypt is a country", metadata={})],

    [Document(page_content="China's Capital is Beijing", metadata={}),
     Document(page_content="China is a country", metadata={}),
     Document(page_content="South Korea's Capital is Seoul", metadata={}),
     Document(page_content="South Korea is a country", metadata={}),
     Document(page_content="Indonesia's Capital is Jakarta", metadata={}),
     Document(page_content="Indonesia is a country", metadata={})]
]
for retrived_docs in docs:
    retrieval_gpt_generate("What is capital of france",retrived_docs)
```
```
6
6
6
6
6
6
```

**dosubot[bot]:**
Hi, @realliyifei. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- The issue involves the Chroma vector store persisting data across iterations despite `persist_directory=None`.
- You reported this as a bug, and @keenborder786 confirmed the issue by showing that in-memory storage is reused within a single Python process.
- A temporary workaround involves resetting the Chroma instance or creating new collections for each iteration.
- @keenborder786 mentioned there's no quick fix without using separate processes.

**Next Steps**
- Please confirm if this issue is still relevant with the latest version of LangChain. If so, you can keep the discussion open by commenting here.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
