# [BUG] Crewai agent can't understand Image URL/Local image path/Base64 for multimodal=True

**Issue #4016** | State: closed | Created: 2025-12-02 | Updated: 2026-03-13
**Author:** kaifeng-cmd
**Labels:** bug, no-issue-activity

### Description

When using `multimodal=True` in CrewAI's LLM agent, image inputs (URLs, local paths) seems like they are treated as plain text instead of multimodal content. This prevents VLMs from processing images, leading to hallucinations or irrelevant outputs. The docs suggest `multimodal=True` auto-adds an **AddImageTool** for URL handling, but it doesn't convert/process links into usable formats (e.g., base64 data), so the LLM sees them as raw strings.

This breaks simple tasks like "Read text from this menu image and list the dishes." Direct LLM API calls work fine with the same images/LLM models, confirming the issue is in CrewAI's agent encapsulation.

The direct LLM APIs call works with image link (I tested with **3 different LLM service providers**). Below roughly shows how they works:

**For Gemini Google Studio**
```
import os
import requests
import base64
from google.generativeai import GenerativeModel

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

model = GenerativeModel("gemini-2.5-flash")

# Fetch and encode image
url = "https://www.englishclub.com/images/vocabulary/food/restaurants/menu-1600.png"
image_data = requests.get(url).content
image_b64 = base64.b64encode(image_data).decode('utf-8')

response = model.generate_content([
    "Describe the dessert in this menu image.",
    {"mime_type": "image/png", "data": image_b64}
])
print(response.text)
```

**VLM from Hugging Face Model**
```
import os
from openai import OpenAI  # Compatible with HF router

hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise ValueError("HF_TOKEN not found")

client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=hf_token)

completion = client.chat.completions.create(
    model="Qwen/Qwen3-VL-7B-Instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe the dessert in this menu image."},
                {"type": "image_url", "image_url": {"url": "https://www.englishclub.com/images/vocabulary/food/restaurants/menu-1600.png"}}
            ]
        }
    ],
    max_tokens=500
)
print(completion.choices[0].message.content)
```

**VLM from Openrouter**
```
import os
import requests
import base64

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found")

url = "https://www.englishclub.com/images/vocabulary/food/restaurants/menu-1600.png"
image_data = requests.get(url).content
image_b64 = base64.b64encode(image_data).decode('utf-8')

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "nvidia/nemotron-nano-12b-v2-vl:free",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Look at this menu image and describe."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
        }
    ],
    "max_tokens": 500
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
print(response.json()["choices"][0]["message"]["content"])
```

All these succeed to read the words in the image link and give correct output. Due to security, Gemini seems like download the URL image link and then convert to base64 and use inline variable to handle. Hugging Face official inference client API support pass the image link and then handle internally via `"type": "image_url"`. Openrouter can handle base64 by setting `"type": "image_url"`.

These confirm VLMs handle images correctly—CrewAI's `multimodal=True` isn't bridging the gap (no fetch/convert to base64/inline). 

### Steps to Reproduce

```
from crewai import Agent, Task, Crew, LLM

llm = LLM(model="gemini/gemini-2.5-flash") # VLM ability

# Ensure .env have GEMINI_API_KEY already
agent = Agent(
    role="Vision Analyst",
    goal="Analyze images and extract text.",
    backstory="You describe visual content accurately.",
    llm=llm,
    verbose=True,
    multimodal=True,
    allow_delegation=False
)

task = Task(
    description="Look at this menu image and describe the words you saw: https://www.englishclub.com/images/vocabulary/food/restaurants/menu-1600.png",
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
print(result)  # Output: Hallucinated
```

### Expected behavior

Agent uses internal AddImageTool to fetch/convert URL to base64/inline data, passes to VLM, outputs accurate description after setting `multimodal=True`.

**Actual Condition**: Seems like treating URL as plain text; VLM hallucinates and output irrelevant content.

### Screenshots/Code snippets

Lets said input this URL: https://www.englishclub.com/images/vocabulary/food/restaurants/menu-1600.png

the image is like this:

LLM is fixed. When I ask "**What desserts in this image link?**"

For `multimodal=True`, respond with
```
Based on the menu in the image you provided, here are the delicious desserts available:

*   Apple Crumble
*   Chocolate Fudge Cake
*   Ice Cream (vanilla, chocolate, strawberry)
*   Fresh Fruit Salad
*   Cheesecake

Sounds like a wonderful selection! Let me know if you need help with anything else.
```
It is random guess for dessert and highly hallucinations becuz it don't know the url link content.

For LLM direct call API (like the code I shown in the description) or Use custom tool to convert URL to base64 and internally call LLM API directly, the result is
```
I'd be happy to help with that! Looking at the menu image you provided, the desserts listed are:   
                                   
*   Apple Pie with Cream                                                                                                             
*   Lemon Meringue Pie                                                                                                               
*   Vanilla Ice Cream                                                    
*   Crêpe Suzette                                                             
*   Fruit Salad                                                                                                                                                                                                                                                                                         
I hope this helps satisfy your sweet tooth! Let me know if there's anything else I can assist you with.   
```

### Operating System

Windows 11

### Python Version

3.11

### crewAI Version

1.2.1

### crewAI Tools Version

1.2.1

### Virtual Environment

Venv

### Evidence

For VisionTool issue (look at additional context section):

### Possible Solution

In `multimodal=True` flow, after input image URL, can handle it by converting to base64 or something compatible with LLM API. I make a custom vision tool for internally use LLM API to read the image, which can accepts image url links/local image path and then convert into base64, then use the API call code from official LLM service providers for handling image to text, and it is SUCEED.

Gemini uses inline
```
{
    "contents": [{
        "parts": [
            {"text": question},
            {"inline_data": {"mime_type": "...", "data": base64}}
        ]
    }]
}
```

HF accepts direct URL and uses 
```
{"type": "image_url", "image_url": {"url": "https://xxx"}}
```

Openrouter uses 
```
{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
```

**NOTE:** I also tried to make a custom for just URL-base64 convertor only, and then pass the tool output to the crewai defined agent, but it cannot handle with base64 too.

### Additional context

I heard someone in the community said can use **import VisionTool from crewai_tools**, and don't use multimodal: `multimodal=False`, but it comes with the output of hitting OpenAI API quota errors when I used other LLM service providers. Although docs said set `OPENAI_API_KEY` but it doesn't explicitly mentioned this tool didn't support for non-OpenAI LLMs (e.g., Gemini/HF), I assume this tool only can support OpenAI LLM, so docs don't note this limitation, which is quite misleading.

## Comments

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

**aleenageorge117:**
Reopen Request: Multimodal Image Handling Broken

Hi team, I've done extensive testing and can confirm the multimodal image functionality is fundamentally broken due to a message handling bug in `crew_agent_executor.py`. This causes LLMs to hallucinate completely unrelated content instead of analyzing the actual images provided.

---

## Root Cause

**Location**: `crewai/agents/crew_agent_executor.py` - Line 309  
**Method**: `_handle_agent_action`

### Current Code (Buggy)
```python
# Line 309
self.messages.append({"role": "assistant", "content": tool_result.result})
```

### The Problem
This line incorrectly wraps `AddImageTool`'s output, creating a nested dictionary that breaks the multimodal message format expected by LLMs.

**What `AddImageTool` returns** (correct OpenAI multimodal format):
```python
{
    "role": "user",
    "content": [
        {"type": "text", "text": "Analyze this image..."},
        {"type": "image_url", "image_url": {"url": "https://..."}}
    ]
}
```

**What line 309 creates** (broken nested structure):
```python
{
    "role": "assistant",        # Wrong role?!
    "content": {                 # Should be array, not dict!
        "role": "user",
        "content": [multimodal array]
    }
}
```

**After JSON serialization** (sent to LiteLLM/Azure):
```json
{
    "role": "assistant",
    "content": "{\"role\": \"user\", \"content\": [{\"type\": \"text\"...}]}"
}
```

The multimodal `content` array is now a **string** instead of structured data. The LLM receives **no image data**.

---

## Reproducible Evidence

### Test Setup
- **Agent**: `multimodal=True`, Azure GPT-4.1 via LiteLLM
- **Task**: "Analyze image at [S3_URL] and list 3 major colors"  
- **Actual Image**: Two Northern Cardinals (red male, gray female) in flight

### Results: LLM Hallucinates Different Objects Every Run

| Run | LLM Output | Actual Content |
|-----|------------|----------------|
| 1 | **White sneakers** with gray/blue accents | Two birds |
| 2 | **PlayStation controller** on MacBook | Two birds |
| 3 | **Tennis ball** on blue court | Two birds |
| 4 | **MacBook workspace** setup | Two birds |
| 5 | **Office desk** with laptop and coffee | Two birds |

The **random, inconsistent hallucinations** prove the LLM isn't receiving the actual image data.

### Proof: Standalone Tool Works Perfectly

Using the **same Azure connection** and **identical S3 image URL** with LiteLLM directly:

```python
response = litellm.completion(
    model="azure/gpt-4.1",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "List food items visible"},
            {"type": "image_url", "image_url": {"url": "https://s3..."}}
        ]
    }]
)
```

**Result**: Correctly identifies **"Two Northern Cardinals in flight"** every single time.

This confirms:
- Azure handles external URLs correctly
- LiteLLM processes multimodal format properly
- The image is accessible and valid
- **CrewAI's line 309 is breaking the message structure**

---

##  Proposed Fix

### Option 1: Smart Message Handling (Recommended)

```python
# Line 309 in crew_agent_executor.py
def _handle_agent_action(self, agent_action, tool_result):
    # ... existing code ...
    
    # Check if tool returned a complete message dict (like AddImageTool)
    if isinstance(tool_result.result, dict) and \
       "role" in tool_result.result and \
       "content" in tool_result.result:
        # Tool already formatted the message - append directly
        self.messages.append(tool_result.result)
    else:
        # Legacy behavior: wrap plain string results
        self.messages.append({"role": "user", "content": str(tool_result.result)})
```

This preserves backward compatibility while fixing multimodal tools.

### Option 2: Direct Append (Simpler)

```python
# Line 309 - just append the result directly
self.messages.append(tool_result.result)
```

Requires all tools to return properly formatted message dicts, but it's cleaner architecturally.

---

##  Debug Traces

I've captured detailed traces showing:
1. Tool is called with correct image URL
2. Tool returns correct multimodal format
3. Message gets incorrectly nested before LLM call
4. LLM hallucinates due to missing image data

---

## Impact

This bug makes **all multimodal agents completely unreliable** for production:
- No errors are thrown (silent failure)
- Tools appear to work
- LLMs confidently describe wrong content
- Impossible to trust any vision analysis outputs

---

Thank you for maintaining this framework!

**siriuslan:**
> Reopen Request: Multimodal Image Handling Broken
> 
> Hi team, I've done extensive testing and can confirm the multimodal image functionality is fundamentally broken due to a message handling bug in `crew_agent_executor.py`. This causes LLMs to hallucinate completely unrelated content instead of analyzing the actual images provided.
> 
> ## Root Cause
> **Location**: `crewai/agents/crew_agent_executor.py` - Line 309 **Method**: `_handle_agent_action`
> 
> ### Current Code (Buggy)
> # Line 309
> self.messages.append({"role": "assistant", "content": tool_result.result})
> ### The Problem
> This line incorrectly wraps `AddImageTool`'s output, creating a nested dictionary that breaks the multimodal message format expected by LLMs.
> 
> **What `AddImageTool` returns** (correct OpenAI multimodal format):
> 
> {
>     "role": "user",
>     "content": [
>         {"type": "text", "text": "Analyze this image..."},
>         {"type": "image_url", "image_url": {"url": "https://..."}}
>     ]
> }
> **What line 309 creates** (broken nested structure):
> 
> {
>     "role": "assistant",        # Wrong role?!
>     "content": {                 # Should be array, not dict!
>         "role": "user",
>         "content": [multimodal array]
>     }
> }
> **After JSON serialization** (sent to LiteLLM/Azure):
> 
> {
>     "role": "assistant",
>     "content": "{\"role\": \"user\", \"content\": [{\"type\": \"text\"...}]}"
> }
> The multimodal `content` array is now a **string** instead of structured data. The LLM receives **no image data**.
> 
> ## Reproducible Evidence
> ### Test Setup
> * **Agent**: `multimodal=True`, Azure GPT-4.1 via LiteLLM
> * **Task**: "Analyze image at [S3_URL] and list 3 major colors"
> * **Actual Image**: Two Northern Cardinals (red male, gray female) in flight
> 
> ### Results: LLM Hallucinates Different Objects Every Run
> Run	LLM Output	Actual Content
> 1	**White sneakers** with gray/blue accents	Two birds
> 2	**PlayStation controller** on MacBook	Two birds
> 3	**Tennis ball** on blue court	Two birds
> 4	**MacBook workspace** setup	Two birds
> 5	**Office desk** with laptop and coffee	Two birds
> The **random, inconsistent hallucinations** prove the LLM isn't receiving the actual image data.
> 
> ### Proof: Standalone Tool Works Perfectly
> Using the **same Azure connection** and **identical S3 image URL** with LiteLLM directly:
> 
> response = litellm.completion(
>     model="azure/gpt-4.1",
>     messages=[{
>         "role": "user",
>         "content": [
>             {"type": "text", "text": "List food items visible"},
>             {"type": "image_url", "image_url": {"url": "https://s3..."}}
>         ]
>     }]
> )
> **Result**: Correctly identifies **"Two Northern Cardinals in flight"** every single time.
> 
> This confirms:
> 
> * Azure handles external URLs correctly
> * LiteLLM processes multimodal format properly
> * The image is accessible and valid
> * **CrewAI's line 309 is breaking the message structure**
> 
> ## Proposed Fix
> ### Option 1: Smart Message Handling (Recommended)
> # Line 309 in crew_agent_executor.py
> def _handle_agent_action(self, agent_action, tool_result):
>     # ... existing code ...
>     
>     # Check if tool returned a complete message dict (like AddImageTool)
>     if isinstance(tool_result.result, dict) and \
>        "role" in tool_result.result and \
>        "content" in tool_result.result:
>         # Tool already formatted the message - append directly
>         self.messages.append(tool_result.result)
>     else:
>         # Legacy behavior: wrap plain string results
>         self.messages.append({"role": "user", "content": str(tool_result.result)})
> This preserves backward compatibility while fixing multimodal tools.
> 
> ### Option 2: Direct Append (Simpler)
> # Line 309 - just append the result directly
> self.messages.append(tool_result.result)
> Requires all tools to return properly formatted message dicts, but it's cleaner architecturally.
> 
> ## Debug Traces
> I've captured detailed traces showing:
> 
> 1. Tool is called with correct image URL
> 2. Tool returns correct multimodal format
> 3. Message gets incorrectly nested before LLM call
> 4. LLM hallucinates due to missing image data
> 
> ## Impact
> This bug makes **all multimodal agents completely unreliable** for production:
> 
> * No errors are thrown (silent failure)
> * Tools appear to work
> * LLMs confidently describe wrong content
> * Impossible to trust any vision analysis outputs
> 
> Thank you for maintaining this framework!

I think your spot the right place however the fix was not good enough, there is chance that tool_result.result is a string which looks like "{'role': 'user', 'content': ...}". 
I made a slight change on top of your fix which works for me however another issue emerged, still working on it.

**gvelesandro:**
Hi, I run Agents Need Context and I am researching failures where multimodal agents appear capable on paper but lose the actual image context they need at runtime.

Your report is a strong example because `multimodal=true` exists, but the image URL is treated like plain text, so the agent guesses instead of seeing the visual input it was supposed to reason over.

If you are open to it, I would value one short postmortem here: https://www.agentsneedcontext.com/agent-failure-postmortem

I am looking for five things: what the agent was trying to do, what context failed to reach it, where that context should have lived, what workaround you used, and what it cost. No pitch, just research.
