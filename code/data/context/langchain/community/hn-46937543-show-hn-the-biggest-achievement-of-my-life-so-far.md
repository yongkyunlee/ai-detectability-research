# Show HN: The biggest achievement of my life so far

**HN** | Points: 9 | Comments: 5 | Date: 2026-02-08
**Author:** ambitious_potat
**HN URL:** https://news.ycombinator.com/item?id=46937543
**Link:** https://github.com/adityaprasad-sudo/Explore-Singapore

Hello everyone,I have always loved coding and in the couple I was thinking of making an open source project and it turned out to be awesome I hope you guys like it.I present Explore Singapore which I created as an open-source intelligence engine to execute retrieval-augmented generation (RAG) on Singapore's public policy documents and legal statutes and historical archives.The objective required building a domain-specific search engine which enables LLM systems to decrease errors by using government documents as their exclusive information source.What my Project does :- basically it provides legal information faster and reliable(due to RAG) without going through long PDFs of goverment websites and helps travellers get insights faster about Singapore.Target Audience:- Python developers who keep hearing about "RAG" and AI agents but haven't build one yet or building one and are stuck somewhere also Singaporean people(obviously!)Comparison:- RAW LLM vs RAG based LLM to test the rag implementation i compared output of my logic code against the standard(gemini&#x2F;Arcee AI&#x2F;groq) and custom system instructions with rag(gemini&#x2F;Arcee AI&#x2F;groq) results were shocking query:- "can I fly in a drone in public park" standard llm response :- ""gave generic advice about "checking local laws"  and safety guidelines""
Customized llm with RAG :- ""cited the air navigation act,specified the 5km no fly zones,and linked to the CAAS permit page"" the difference was clear and it was sure that the ai was not hallucinating.Ingestion:- I have the RAG Architecture about 594 PDFs about Singaporian laws and acts which rougly contains 33000 pages.How did I do it :- I used google Collab to build vector database and metadata which nearly took me 1 hour to do so ie convert PDFs to vectors.How accurate is it:- It's still in development phase but still it provides near accurate information as it contains multi query retrieval ie if a user asks ("ease of doing business in Singapore") the logic would break the keywords "ease", "business", "Singapore" and provide the required documents from the PDFs with the page number also it's a little hard to explain but you can check it on my webpage.Its not perfect but hey i am still learning.The Tech Stack:  
Ingestion: Python scripts using PyPDF2 to parse various PDF formats.  
Embeddings: Hugging Face BGE-M3(1024 dimensions)
Vector Database: FAISS for similarity search.  
Orchestration: LangChain.  
Backend: Flask
Frontend: React and Framer.The RAG Pipeline operates through the following process:  
Chunking: The source text is divided into chunks of 150 with an overlap of 50 tokens to maintain context across boundaries.  
Retrieval: When a user asks a question (e.g., "What is the policy on HDB grants?"), the system queries the vector database for the top k chunks (k=1).  
Synthesis: The system adds these chunks to the prompt of LLMs which produces the final response that includes citation information.
Why did I say llms :- because I wanted the system to be as non crashable as possible so I am using gemini as my primary llm to provide responses but if it fails to do so due to api requests or any other reasons the backup model(Arcee AI trinity large) can handle the requests.Don't worry :- I have implemented different system instructions for different models so that result is a good quality product.Current Challenges:  
I am working on optimizing the the ranking strategy of the RAG architecture. I would value insights from anyone who has encountered RAG returning unrelevant documents.Feedbacks are the backbone of improving a platform so they are mostRepository:- https:&#x2F;&#x2F;github.com&#x2F;adityaprasad-sudo&#x2F;Explore-Singapore

## Top Comments

**ambitious_potat:**
Oh hey i forgot to mention here's the live demo:-
https:&#x2F;&#x2F;adityaprasad-sudo.github.io&#x2F;Explore-Singapore&#x2F;

**jasonmarconi334:**
Intresting work my friend really love that glass morphism on the web page

**drakeswalla:**
dude definatly this prevent hallucinations haha

**drakeswalla:**
mind if i ask why did you create the vector database on google collab
