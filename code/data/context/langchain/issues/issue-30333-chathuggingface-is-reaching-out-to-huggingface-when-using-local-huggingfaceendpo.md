# `ChatHuggingface` is reaching out to huggingface when using local `HuggingFaceEndpoint`

**Issue #30333** | State: open | Created: 2025-03-17 | Updated: 2026-03-15
**Author:** JoeSF49
**Labels:** help wanted, bug, integration, huggingface, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

Setting ChatHuggingFace llm param to locally hosted HuggingFaceEndpoint is trying to reach out to hugginface website and failing on air-gapped system.

i recieve 401s and 404s due to api trying to reach and login to hugginface instead of using HuggingFaceEndpoint.  When i invoke HuggingFaceEndpoint directly I receive response needed.  I'm trying to load it into ChatHuggingFace so that I may hopefully use "with_structured_output"

### Error Message and Stack Trace (if applicable)

system is air-gapped and i cannot transfer from it.   i recieve 401s and 404s due to api trying to reach and login to hugginface instead of using HuggingFaceEndpoint.

### Description

i recieve 401s and 404s due to api trying to reach and login to hugginface instead of using HuggingFaceEndpoint.  When i invoke HuggingFaceEndpoint directly I receive response needed.  I'm trying to load it into ChatHuggingFace so that I may hopefully use "with_structured_output"

### System Info

airgapped but rebuilt using 0.3.45

## Comments

**dhruva71:**
Can you explain how you are running the model locally so that we have more details? 

I understand the documentation does show an example with localhost, but that seems to be an example only. From what I see in the code, it only supports connecting and running inference from HuggingFace Hub.

**JoeSF49:**
I run all LLMs locally on the same server as LangChain code.  I'm using HuggingsFace's Text Generation Interface (TGI) docker workload to serve it as an API endpoint hence the usage of "HuggingFaceEndpoint".   Once loaded i'm trying to use, ChatHuggingFace to leverage the "with_structured_output" as HuggingFaceEndpoint does not support that directive.  

ChatHuggingFace documentation states..  "You can instantiate a ChatHuggingFace model in two different ways, either from a HuggingFaceEndpoint or from a HuggingFacePipeline."   

Per...
https://python.langchain.com/docs/integrations/chat/huggingface/#instantiation

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    repo_id="HuggingFaceH4/zephyr-7b-beta",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03,
)

chat_model = ChatHuggingFace(llm=llm)
 

I have a HuggingFaceEndpoint however the library still attempts to reach out to Huggingface hub over internet.  why is it doing this when i've already given it the local HuggingFaceEndpoint?

**dhruva71:**
Thanks a lot for the details. 

I see an `endpoint_url` parameter available in the parameters of `HuggingFaceEndpoint`. Could you try passing that in and pointing it to the TGI?

**JoeSF49:**
I don't have an issue using huggingfaceendpoint.  I use it all the time
with endpoint.  My issue is using chathuggingface.  When passing
huggingfaceendpoint, using local endpoint, chathuggingface still tries to
egress to Internet

On Sat, Mar 22, 2025, 13:18 Dhruvajyoti Sarma ***@***.***>
wrote:

> Thanks a lot for the details.
>
> I see an endpoint_url parameter available in the parameters of
> HuggingFaceEndpoint. Could you try passing that in and pointing it to the
> TGI?
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you authored the thread.Message ID:
> ***@***.***>
> [image: dhruva71]*dhruva71* left a comment (langchain-ai/langchain#30333)
> 
>
> Thanks a lot for the details.
>
> I see an endpoint_url parameter available in the parameters of
> HuggingFaceEndpoint. Could you try passing that in and pointing it to the
> TGI?
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you authored the thread.Message ID:
> ***@***.***>
>

**daniau23:**
@dhruva71 I recently made use of the HuggingFaceEndpoint with mistralai/Mistral-7B-Instruct-v0.3 some days ago and it worked well but today it's  not working  

```# loadding Huggingface token
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# models 
repo_id = "mistralai/Mistral-7B-Instruct-v0.3"

# model parameters
model_kwargs = {
    # "max_new_tokens": 1000, # Maximum tokens to generate
    # "max_length": 4000, # Maximum length of input + output
    "temperature": 0.1, # Controls randomness of output
    "timeout": 6000,
    # "task":'conversational'
}

# LLM set up
llm = HuggingFaceEndpoint(
    repo_id=repo_id,
    huggingfacehub_api_token = HUGGINGFACEHUB_API_TOKEN,
    # you specify the task or not
    # You can also specify the task in the model_kwargs or within here
    # task = 'conversational',
    **model_kwargs,
)
```

```
search_kwargs = {"k":4}

retriever = db.as_retriever(search_kwargs=search_kwargs)
qa = RetrievalQAWithSourcesChain.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever = retriever
)

input_data = {
    "question": "what did Mehedi Tajrian discover in there research?"
}
d_response = qa.invoke(input_data)
```

### Error
```
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Cell In[73], line 4
      1 input_data = {
      2     "question": "what did Mehedi Tajrian discover in there research?"
      3 }
----> 4 d_response = qa.invoke(input_data)

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:167, in Chain.invoke(self, input, config, **kwargs)
    165 except BaseException as e:
    166     run_manager.on_chain_error(e)
--> 167     raise e
    168 run_manager.on_chain_end(outputs)
    170 if include_run_info:

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:157, in Chain.invoke(self, input, config, **kwargs)
    154 try:
    155     self._validate_inputs(inputs)
    156     outputs = (
--> 157         self._call(inputs, run_manager=run_manager)
    158         if new_arg_supported
    159         else self._call(inputs)
    160     )
    162     final_outputs: dict[str, Any] = self.prep_outputs(
    163         inputs, outputs, return_only_outputs
    164     )
    165 except BaseException as e:

File \llmai\llm_deep\Lib\site-packages\langchain\chains\qa_with_sources\base.py:166, in BaseQAWithSourcesChain._call(self, inputs, run_manager)
    163 else:
    164     docs = self._get_docs(inputs)  # type: ignore[call-arg]
--> 166 answer = self.combine_documents_chain.run(
    167     input_documents=docs, callbacks=_run_manager.get_child(), **inputs
    168 )
    169 answer, sources = self._split_sources(answer)
    170 result: dict[str, Any] = {
    171     self.answer_key: answer,
    172     self.sources_answer_key: sources,
    173 }

File \llmai\llm_deep\Lib\site-packages\langchain_core\_api\deprecation.py:191, in deprecated..deprecate..warning_emitting_wrapper(*args, **kwargs)
    189     warned = True
    190     emit_warning()
--> 191 return wrapped(*args, **kwargs)

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:608, in Chain.run(self, callbacks, tags, metadata, *args, **kwargs)
    603     return self(args[0], callbacks=callbacks, tags=tags, metadata=metadata)[
    604         _output_key
    605     ]
    607 if kwargs and not args:
--> 608     return self(kwargs, callbacks=callbacks, tags=tags, metadata=metadata)[
    609         _output_key
    610     ]
    612 if not kwargs and not args:
    613     raise ValueError(
    614         "`run` supported with either positional arguments or keyword arguments,"
    615         " but none were provided."
    616     )

File \llmai\llm_deep\Lib\site-packages\langchain_core\_api\deprecation.py:191, in deprecated..deprecate..warning_emitting_wrapper(*args, **kwargs)
    189     warned = True
    190     emit_warning()
--> 191 return wrapped(*args, **kwargs)

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:386, in Chain.__call__(self, inputs, return_only_outputs, callbacks, tags, metadata, run_name, include_run_info)
    354 """Execute the chain.
    355 
    356 Args:
   (...)
    377         `Chain.output_keys`.
    378 """
    379 config = {
    380     "callbacks": callbacks,
    381     "tags": tags,
    382     "metadata": metadata,
    383     "run_name": run_name,
    384 }
--> 386 return self.invoke(
    387     inputs,
    388     cast(RunnableConfig, {k: v for k, v in config.items() if v is not None}),
    389     return_only_outputs=return_only_outputs,
    390     include_run_info=include_run_info,
    391 )

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:167, in Chain.invoke(self, input, config, **kwargs)
    165 except BaseException as e:
    166     run_manager.on_chain_error(e)
--> 167     raise e
    168 run_manager.on_chain_end(outputs)
    170 if include_run_info:

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:157, in Chain.invoke(self, input, config, **kwargs)
    154 try:
    155     self._validate_inputs(inputs)
    156     outputs = (
--> 157         self._call(inputs, run_manager=run_manager)
    158         if new_arg_supported
    159         else self._call(inputs)
    160     )
    162     final_outputs: dict[str, Any] = self.prep_outputs(
    163         inputs, outputs, return_only_outputs
    164     )
    165 except BaseException as e:

File \llmai\llm_deep\Lib\site-packages\langchain\chains\combine_documents\base.py:138, in BaseCombineDocumentsChain._call(self, inputs, run_manager)
    136 # Other keys are assumed to be needed for LLM prediction
    137 other_keys = {k: v for k, v in inputs.items() if k != self.input_key}
--> 138 output, extra_return_dict = self.combine_docs(
    139     docs, callbacks=_run_manager.get_child(), **other_keys
    140 )
    141 extra_return_dict[self.output_key] = output
    142 return extra_return_dict

File \llmai\llm_deep\Lib\site-packages\langchain\chains\combine_documents\stuff.py:259, in StuffDocumentsChain.combine_docs(self, docs, callbacks, **kwargs)
    257 inputs = self._get_inputs(docs, **kwargs)
    258 # Call predict on the LLM.
--> 259 return self.llm_chain.predict(callbacks=callbacks, **inputs), {}

File \llmai\llm_deep\Lib\site-packages\langchain\chains\llm.py:319, in LLMChain.predict(self, callbacks, **kwargs)
    304 def predict(self, callbacks: Callbacks = None, **kwargs: Any) -> str:
    305     """Format prompt with kwargs and pass to LLM.
    306 
    307     Args:
   (...)
    317             completion = llm.predict(adjective="funny")
    318     """
--> 319     return self(kwargs, callbacks=callbacks)[self.output_key]

File \llmai\llm_deep\Lib\site-packages\langchain_core\_api\deprecation.py:191, in deprecated..deprecate..warning_emitting_wrapper(*args, **kwargs)
    189     warned = True
    190     emit_warning()
--> 191 return wrapped(*args, **kwargs)

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:386, in Chain.__call__(self, inputs, return_only_outputs, callbacks, tags, metadata, run_name, include_run_info)
    354 """Execute the chain.
    355 
    356 Args:
   (...)
    377         `Chain.output_keys`.
    378 """
    379 config = {
    380     "callbacks": callbacks,
    381     "tags": tags,
    382     "metadata": metadata,
    383     "run_name": run_name,
    384 }
--> 386 return self.invoke(
    387     inputs,
    388     cast(RunnableConfig, {k: v for k, v in config.items() if v is not None}),
    389     return_only_outputs=return_only_outputs,
    390     include_run_info=include_run_info,
    391 )

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:167, in Chain.invoke(self, input, config, **kwargs)
    165 except BaseException as e:
    166     run_manager.on_chain_error(e)
--> 167     raise e
    168 run_manager.on_chain_end(outputs)
    170 if include_run_info:

File \llmai\llm_deep\Lib\site-packages\langchain\chains\base.py:157, in Chain.invoke(self, input, config, **kwargs)
    154 try:
    155     self._validate_inputs(inputs)
    156     outputs = (
--> 157         self._call(inputs, run_manager=run_manager)
    158         if new_arg_supported
    159         else self._call(inputs)
    160     )
    162     final_outputs: dict[str, Any] = self.prep_outputs(
    163         inputs, outputs, return_only_outputs
    164     )
    165 except BaseException as e:

File \llmai\llm_deep\Lib\site-packages\langchain\chains\llm.py:127, in LLMChain._call(self, inputs, run_manager)
    122 def _call(
    123     self,
    124     inputs: dict[str, Any],
    125     run_manager: Optional[CallbackManagerForChainRun] = None,
    126 ) -> dict[str, str]:
--> 127     response = self.generate([inputs], run_manager=run_manager)
    128     return self.create_outputs(response)[0]

File \llmai\llm_deep\Lib\site-packages\langchain\chains\llm.py:139, in LLMChain.generate(self, input_list, run_manager)
    137 callbacks = run_manager.get_child() if run_manager else None
    138 if isinstance(self.llm, BaseLanguageModel):
--> 139     return self.llm.generate_prompt(
    140         prompts,
    141         stop,
    142         callbacks=callbacks,
    143         **self.llm_kwargs,
    144     )
    145 else:
    146     results = self.llm.bind(stop=stop, **self.llm_kwargs).batch(
    147         cast(list, prompts), {"callbacks": callbacks}
    148     )

File \llmai\llm_deep\Lib\site-packages\langchain_core\language_models\llms.py:764, in BaseLLM.generate_prompt(self, prompts, stop, callbacks, **kwargs)
    755 @override
    756 def generate_prompt(
    757     self,
   (...)
    761     **kwargs: Any,
    762 ) -> LLMResult:
    763     prompt_strings = [p.to_string() for p in prompts]
--> 764     return self.generate(prompt_strings, stop=stop, callbacks=callbacks, **kwargs)

File \llmai\llm_deep\Lib\site-packages\langchain_core\language_models\llms.py:971, in BaseLLM.generate(self, prompts, stop, callbacks, tags, metadata, run_name, run_id, **kwargs)
    956 if (self.cache is None and get_llm_cache() is None) or self.cache is False:
    957     run_managers = [
    958         callback_manager.on_llm_start(
    959             self._serialized,
   (...)
    969         )
    970     ]
--> 971     return self._generate_helper(
    972         prompts,
    973         stop,
    974         run_managers,
    975         new_arg_supported=bool(new_arg_supported),
    976         **kwargs,
    977     )
    978 if len(missing_prompts) > 0:
    979     run_managers = [
    980         callback_managers[idx].on_llm_start(
    981             self._serialized,
   (...)
    988         for idx in missing_prompt_idxs
    989     ]

File \llmai\llm_deep\Lib\site-packages\langchain_core\language_models\llms.py:790, in BaseLLM._generate_helper(self, prompts, stop, run_managers, new_arg_supported, **kwargs)
    779 def _generate_helper(
    780     self,
    781     prompts: list[str],
   (...)
    786     **kwargs: Any,
    787 ) -> LLMResult:
    788     try:
    789         output = (
--> 790             self._generate(
    791                 prompts,
    792                 stop=stop,
    793                 # TODO: support multiple run managers
    794                 run_manager=run_managers[0] if run_managers else None,
    795                 **kwargs,
    796             )
    797             if new_arg_supported
    798             else self._generate(prompts, stop=stop)
    799         )
    800     except BaseException as e:
    801         for run_manager in run_managers:

File \llmai\llm_deep\Lib\site-packages\langchain_core\language_models\llms.py:1545, in LLM._generate(self, prompts, stop, run_manager, **kwargs)
   1542 new_arg_supported = inspect.signature(self._call).parameters.get("run_manager")
   1543 for prompt in prompts:
   1544     text = (
-> 1545         self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
   1546         if new_arg_supported
   1547         else self._call(prompt, stop=stop, **kwargs)
   1548     )
   1549     generations.append([Generation(text=text)])
   1550 return LLMResult(generations=generations)

File \llmai\llm_deep\Lib\site-packages\langchain_huggingface\llms\huggingface_endpoint.py:312, in HuggingFaceEndpoint._call(self, prompt, stop, run_manager, **kwargs)
    310     return completion
    311 else:
--> 312     response_text = self.client.text_generation(
    313         prompt=prompt,
    314         model=self.model,
    315         **invocation_params,
    316     )
    318     # Maybe the generation has stopped at one of the stop sequences:
    319     # then we remove this stop sequence from the end of the generated text
    320     for stop_seq in invocation_params["stop"]:

File \llmai\llm_deep\Lib\site-packages\huggingface_hub\inference\_client.py:2298, in InferenceClient.text_generation(self, prompt, details, stream, model, adapter_id, best_of, decoder_input_details, do_sample, frequency_penalty, grammar, max_new_tokens, repetition_penalty, return_full_text, seed, stop, stop_sequences, temperature, top_k, top_n_tokens, top_p, truncate, typical_p, watermark)
   2296 model_id = model or self.model
   2297 provider_helper = get_provider_helper(self.provider, task="text-generation", model=model_id)
-> 2298 request_parameters = provider_helper.prepare_request(
   2299     inputs=prompt,
   2300     parameters=parameters,
   2301     extra_payload={"stream": stream},
   2302     headers=self.headers,
   2303     model=model_id,
   2304     api_key=self.token,
   2305 )
   2307 # Handle errors separately for more precise error messages
   2308 try:

File \llmai\llm_deep\Lib\site-packages\huggingface_hub\inference\_providers\_common.py:67, in TaskProviderHelper.prepare_request(self, inputs, parameters, headers, model, api_key, extra_payload)
     64 api_key = self._prepare_api_key(api_key)
     66 # mapped model from HF model ID
---> 67 provider_mapping_info = self._prepare_mapping_info(model)
     69 # default HF headers + user headers (to customize in subclasses)
     70 headers = self._prepare_headers(headers, api_key)

File \llmai\llm_deep\Lib\site-packages\huggingface_hub\inference\_providers\_common.py:131, in TaskProviderHelper._prepare_mapping_info(self, model)
    128     raise ValueError(f"Model {model} is not supported by provider {self.provider}.")
    130 if provider_mapping.task != self.task:
--> 131     raise ValueError(
    132         f"Model {model} is not supported for task {self.task} and provider {self.provider}. "
    133         f"Supported task: {provider_mapping.task}."
    134     )
    136 if provider_mapping.status == "staging":
    137     logger.warning(
    138         f"Model {model} is in staging mode for provider {self.provider}. Meant for test purposes only."
    139     )

ValueError: Model mistralai/Mistral-7B-Instruct-v0.3 is not supported for task text-generation and provider together. Supported task: conversational.
```

**Devpatel1901:**
@daniau23 The Hugging Face Inference API expects each model to be used with a specific supported task. In your case, you are using `mistralai/Mistral-7B-Instruct-v0.3` which only supports only `conversational` task. But In your code, you are not specifying the task explicitly in your HuggingFaceEndpoint call, So, by default, LangChain assumes `task="text-generation"`, which is not valid for this model.

Can you please uncomment `task` key from your `model-kwargs` dict and try again?

**daniau23:**
@Devpatel1901 I have already resolved this issue last year and written a detailed solution to this via this link [Solution](https://github.com/huggingface/text-generation-inference/issues/3250#issuecomment-2940421732)

**madhumach:**
so could this issue be closed?

**daniau23:**
@madhumach yes, we can.
