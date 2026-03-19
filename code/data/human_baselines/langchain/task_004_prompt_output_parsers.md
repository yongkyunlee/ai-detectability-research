---
source_url: https://blog.langchain.com/going-beyond-chatbots-how-to-make-gpt-4-output-structured-data-using-langchain/
author: "Jacob Lee"
platform: blog.langchain.com
scope_notes: "Trimmed from 'Going Beyond Chatbots: How to Make GPT-4 Output Structured Data Using LangChain'. Focused on the core problem of output parsing and the solution using StructuredOutputParser and OutputFixingParser. Removed lengthy output examples and some additional tips to stay within 300-500 words."
---

Over the past few months, I had the opportunity to do some cool exploratory work for a client that integrated LLMs like GPT-4 and Claude into their internal workflow, rather than exposing them through a chat interface. The general idea was to take some input data, analyze it using an LLM, enrich the LLM's output using existing data sources, and then sanity check it using both traditional tools and LLMs. This process could repeat several times until finally storing a final result in a database.

## The Problem

While building such pipelines, I quickly realized that while natural language is an excellent interface for a chatbot, it's quite a difficult one to use with existing APIs. Naively asking an LLM "Give me a list of 5 countries" results in a numbered list with no guaranteed format. You would need to write awkward custom string parsing logic to extract the data for the next step.

Prompting the LLM to output data in a structured format isn't simple either. Asking "Give me a list of 5 countries, formatted as Airtable records" produces conversational text mixed with assumed field names that likely don't match your internal schema. Adding language like "Output only an array of JSON objects containing X, Y, and Z" to all my prompts quickly became tedious and unreliable due to the non-deterministic nature of LLMs.

## The Solution

After asking around the LangChainJS Discord community, I discovered an elegant, built-in solution: output fixing parsers. They contain two components:

1. An easy, consistent way of generating output formatting instructions using Zod, a popular TypeScript validation framework.
2. An LLM-powered recovery mechanism for handling badly formatted outputs using a more focused prompt.

```javascript
import { z } from "zod";
import { StructuredOutputParser, OutputFixingParser } from "langchain/output_parsers";

const outputParser = StructuredOutputParser.fromZodSchema(
  z.array(
    z.object({
      fields: z.object({
        Name: z.string().describe("The name of the country"),
        Capital: z.string().describe("The country's capital")
      })
    })
  ).describe("An array of Airtable records, each representing a country")
);

const outputFixingParser = OutputFixingParser.fromLLM(chatModel, outputParser);
```

You then use a `PromptTemplate` with `format_instructions` from the parser, chain it with an `LLMChain`, and the result will already be typed as an array of objects — no need for `JSON.parse()` calls or any further parsing. The output fixing parser will throw an error if it can't generate output matching the provided Zod schema.

Descriptions provided with `.describe()` are optional but give the LLM helpful context when populating individual fields. You can also use different model instances in the output fixing parser and your main chain, allowing you to mix and match temperatures and even providers for best results.
