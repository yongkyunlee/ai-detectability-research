# langchain_huggingface - Cannot use chat template functions because tokenizer.chat_template is not set

**Issue #29126** | State: closed | Created: 2025-01-10 | Updated: 2026-03-06
**Author:** Arslan-Mehmood1
**Labels:** external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code


```python

import torch
from transformers import pipeline
from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline

model_id = "meta-llama/Llama-3.2-3B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
# transformers_llm_pipeline = pipeline("text-generation", model_id)

hf_pipe_llm = HuggingFacePipeline(
    pipeline=pipe
)
# hf_pipe_llm = HuggingFacePipeline.from_model_id(
#     model_id = model_id,
#     task = "text-generation",
#     device_map = 'cuda'
# )
tokenizer = AutoTokenizer.from_pretrained(model_id)

print("hf_pipe_llm.pipeline.tokenizer.chat_template -----------")
print(hf_pipe_llm.pipeline.tokenizer.chat_template)
print("hf_pipe_llm.pipeline.tokenizer.chat_template -----------")


hf_text_model = ChatHuggingFace(
    llm = hf_pipe_llm,
    model_id = model_id,
    tokenizer = tokenizer
)

print("hf_text_model.tokenizer.chat_template-----------")
print(hf_text_model.tokenizer.chat_template)
print("hf_text_model.tokenizer.chat_template-----------")

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

messages = [
    SystemMessage(content="You're a helpful assistant"),
    HumanMessage(
        content="What happens when an unstoppable force meets an immovable object?"
    )
]

# ai_msg = hf_text_model.invoke(messages)
# print(ai_msg)

```


### Error Message and Stack Trace (if applicable)

How to resolve?
ERROR:
```
Traceback (most recent call last):
  File "/home/paperspace/Ahmer/privatellm/src/2.py", line 50, in 
    ai_msg = hf_text_model.invoke(messages)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 286, in invoke
    self.generate_prompt(
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 786, in generate_prompt
    return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 643, in generate
    raise e
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 633, in generate
    self._generate_with_cache(
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 851, in _generate_with_cache
    result = self._generate(
             ^^^^^^^^^^^^^^^
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_huggingface/chat_models/huggingface.py", line 373, in _generate
    llm_input = self._to_chat_prompt(messages)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/langchain_huggingface/chat_models/huggingface.py", line 410, in _to_chat_prompt
    return self.tokenizer.apply_chat_template(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/transformers/tokenization_utils_base.py", line 1617, in apply_chat_template
    chat_template = self.get_chat_template(chat_template, tools)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/paperspace/.virtualenvs/privatellm/lib/python3.11/site-packages/transformers/tokenization_utils_base.py", line 1785, in get_chat_template
    raise ValueError(
ValueError: Cannot use chat template functions because tokenizer.chat_template is not set and no template argument was passed! For information about writing templates and setting the tokenizer.chat_template attribute, please see the documentation at https://huggingface.co/docs/transformers/main/en/chat_templating
```

Chat Template:
```
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████| 2/2 [00:01<00:00,  1.06it/s]
Device set to use cuda:0
hf_pipe_llm.pipeline.tokenizer.chat_template -----------
None
hf_pipe_llm.pipeline.tokenizer.chat_template -----------
hf_text_model.tokenizer.chat_template-----------
None
hf_text_model.tokenizer.chat_template-----------
```

### Description

use langchain_huggingface

### System Info

.

## Comments

**Ashish-Abraham:**
Try using a chat model like meta-llama/Llama-3.2-1B-Instruct instead of base one.

**dosubot[bot]:**
Hi, @Arslan-Mehmood1. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- You reported a bug where `tokenizer.chat_template` is not set, affecting chat template functions.
- The issue persists even after updating to the latest version of LangChain.
- The problem occurs specifically with the `ChatHuggingFace` class using a HuggingFace pipeline.
- Ashish-Abraham suggested using a chat model like meta-llama/Llama-3.2-1B-Instruct as a workaround.

**Next Steps:**
- Please confirm if this issue is still relevant with the latest version of LangChain by commenting here.
- If no updates are provided, the issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
