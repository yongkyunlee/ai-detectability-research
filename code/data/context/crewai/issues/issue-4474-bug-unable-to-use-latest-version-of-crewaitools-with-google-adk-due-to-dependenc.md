# [BUG] Unable to use latest version of crewai[tools] with google-adk due to dependency conflict

**Issue #4474** | State: open | Created: 2026-02-13 | Updated: 2026-03-15
**Author:** suruchikeswani
**Labels:** bug, no-issue-activity

### Description

I am trying to use the PDFSearchTool (from crewai_tools import PDFSearchTool) with my ADK agent using the CrewaiTool wrapper provided by google-adk. 
When I try to install the latest versions of google-adk (1.23.0) and crewai[tools] (1.9.3) I see some dependency conflicts for open telemetry-api and other related libraries. Looks like crewai-tools needs 1.34.0 version of this library while google-adk needs a higher one like 1.38.0. Due to this, my pip install fails. If I try to install crewai[tools] first and then google-adk, pip install works, but I get errors when I try to run my ADK agent that uses this crewai tool.
Can you please help?

### Steps to Reproduce

1. pip install google-adk
2. pip install 'crewai[tools]'
Error during step 2:
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.                                                                                                                                
google-adk 1.25.0 requires opentelemetry-api=1.36.0, but you have opentelemetry-api 1.34.1 which is incompatible.                             
google-adk 1.25.0 requires opentelemetry-exporter-otlp-proto-http>=1.36.0, but you have opentelemetry-exporter-otlp-proto-http 1.34.1 which is incompatible.                                                                                                                                                  
google-adk 1.25.0 requires opentelemetry-sdk=1.36.0, but you have opentelemetry-sdk 1.34.1 which is incompatible.                             
opentelemetry-exporter-gcp-logging 1.11.0a0 requires opentelemetry-api>=1.35.0, but you have opentelemetry-api 1.34.1 which is incompatible.           
opentelemetry-exporter-gcp-logging 1.11.0a0 requires opentelemetry-sdk=1.35.0, but you have opentelemetry-sdk 1.34.1 which is incompatible.   
grpcio-status 1.78.0 requires protobuf=6.31.1, but you have protobuf 5.29.6 which is incompatible.                                             

or 
1. pip install 'crewai[tools]'
2. pip install google-adk
3. Both installations successful
4. adk run  : Error  No module named 'crewai_tools'
5. pip install crewai-tools
Error:
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.                                                                                                                                
google-adk 1.25.0 requires opentelemetry-api=1.36.0, but you have opentelemetry-api 1.34.1 which is incompatible.                             
google-adk 1.25.0 requires opentelemetry-exporter-otlp-proto-http>=1.36.0, but you have opentelemetry-exporter-otlp-proto-http 1.34.1 which is incompatible.                                                                                                                                                  
google-adk 1.25.0 requires opentelemetry-sdk=1.36.0, but you have opentelemetry-sdk 1.34.1 which is incompatible.                             
opentelemetry-exporter-gcp-logging 1.11.0a0 requires opentelemetry-api>=1.35.0, but you have opentelemetry-api 1.34.1 which is incompatible.           
opentelemetry-exporter-gcp-logging 1.11.0a0 requires opentelemetry-sdk=1.35.0, but you have opentelemetry-sdk 1.34.1 which is incompatible.   
grpcio-status 1.78.0 requires protobuf=6.31.1, but you have protobuf 5.29.6 which is incompatible. 

### Expected behavior

pip install for both libraries is successful and I am able to use the PDFSearch tool

### Screenshots/Code snippets

root_agent = Agent(
    name="pdf_query_agent",
    description="Agent to answer users questions based on input document",
    instruction="""
        - You are an assistant that has the capability to answer the users questions based on 
        contents of a PDF file
        - Ask the user what they want to know about the PDF file
        - Use your tool to search for the answers to the users question in the PDF file given to it
        """,
    model=os.getenv("MODEL"),
    tools = [
            CrewaiTool(
                name="search_info_in_PDF",
                description=(
                    """Searches for the answers to the user's question in the PDF"""
                ),
                tool = PDFSearchTool(pdf='pdf_reader_agent/')
            )
        ]

)                                   

### Operating System

macOS Sonoma

### Python Version

3.12

### crewAI Version

1.9.3

### crewAI Tools Version

1.9.3

### Virtual Environment

Venv

### Evidence

ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.                                                                                                                                
google-adk 1.25.0 requires opentelemetry-api=1.36.0, but you have opentelemetry-api 1.34.1 which is incompatible.                             
google-adk 1.25.0 requires opentelemetry-exporter-otlp-proto-http>=1.36.0, but you have opentelemetry-exporter-otlp-proto-http 1.34.1 which is incompatible.                                                                                                                                                  
google-adk 1.25.0 requires opentelemetry-sdk=1.36.0, but you have opentelemetry-sdk 1.34.1 which is incompatible.                             
opentelemetry-exporter-gcp-logging 1.11.0a0 requires opentelemetry-api>=1.35.0, but you have opentelemetry-api 1.34.1 which is incompatible.           
opentelemetry-exporter-gcp-logging 1.11.0a0 requires opentelemetry-sdk=1.35.0, but you have opentelemetry-sdk 1.34.1 which is incompatible.   
grpcio-status 1.78.0 requires protobuf=6.31.1, but you have protobuf 5.29.6 which is incompatible.                                             

### Possible Solution

upgrade opentelemetry and other conflicting dependencies with google-adk

### Additional context

NA

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.
