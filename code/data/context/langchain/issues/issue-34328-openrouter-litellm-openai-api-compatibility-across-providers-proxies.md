# OpenRouter / LiteLLM / OpenAI API compatibility across providers / proxies

**Issue #34328** | State: open | Created: 2025-12-12 | Updated: 2026-03-10
**Author:** mdrxy
**Labels:** internal, openrouter, vllm

### Privileged issue

- [x] I am a LangChain maintainer, or was asked directly by a LangChain maintainer to create an issue here.

### Issue Content

Tracking for upcoming OpenRouter integration.

It is not practical for `ChatOpenAI` to handle each addition that third party providers make to the Chat Completions standard.

## Related issues

### OpenRouter

#31325

- User is attempting to access OpenRouter via `ChatAnthropic`
- Recommended to use `ChatOpenAI` with warning.

#32967

- User is attempting to access OpenRouter via `ChatOpenAI`
- Structured output via `create_agent` fails because OpenRouter doesn't support the OpenAI SDK's `beta.chat.completions.parse` method

#32977

- User is attempting to access OpenRouter via `ChatOpenAI`
- `with_structured_output` fails with `JSONDecodeError` when OpenRouter returns malformed/incomplete JSON. Even with `include_raw=True`, the raw response is inaccessible on error.

#32981

- User is attempting to access OpenRouter via `ChatOpenAI`
- Reasoning content is not being captured by `ChatOpenAI`
  - Commenter states `ChatDeepSeek` is also not working

#33643

- User requests native LiteLLM and OpenRouter integrations in LangChain.

#33757

- User wants to use OpenRouter via `ChatOpenAI` to support `cache_control` (e.g. for Anthropic models)

#34056

- User is accessing `gemini-3-pro-preview` with OpenRouter via `ChatOpenAI` but thought signatures are not being handled
- Commenters recommended using `langchain-litellm` as a workaround but it is unclear if this is just compatibility by luck

#34797

- User is attempting to access OpenRouter via `ChatOpenAI`
- `ProviderStrategy` is not working

#34962

- User requesting dedicated `langchain-openrouter` / `ChatOpenRouter` that does not inherit from `BaseChatOpenAI` because
  - Response schema and header contract differ
  - OpenRouter is a distinct provider, not an OpenAI variant
  - Proper tracing requires correct `_llm_type` identification
  - OpenRouter metadata (routing info) needs first-class support

### LiteLLM

#30530

- User is attempting to access a LiteLLM based proxy via `ChatOpenAI`. `reasoning_content` and `thinking_blocks` fields aren't captured by `ChatOpenAI`.
- LiteLLM adds thinking/reasoning on top of the Chat Completions API
- We recommended to use [`langchain-litellm`](https://github.com/Akshay-Dongare/langchain-litellm/)

#33643

- User requests native LiteLLM and OpenRouter integrations in LangChain.

#34891

- User is accessing LiteLLM models via `ChatOpenAI`
- `ToolStrategy` structured output is not working
- Related: #28176

### vLLM

#34307

- User wants to use vLLM via `ChatOpenAI`, we purportedly don't capture `stop_reason`

### General

#34153

- User is asking to extract non-standard reasoning content field from APIs built on top of the Chat Completions API (e.g. vLLM)

#34706

- User is accessing endpoints that build on top of the Chat Completions API (OCI Garthok) via `ChatOpenAI`, `reasoning_content` is not preserved
- Argues that using `ChatXAI` would be semantically incorrect to access OpenAI models via the router/proxy, which is valid. However, OCI Garthok appears to be a service that builds on top of Chat Completions, as `reasoning_content` is not an official field on the spec
- "Handling it once in `BaseChatOpenAI` could avoid this duplication and benefit the broader ecosystem of OpenAI-[based] APIs."
  - "it would be helpful to document which fields are preserved" -- we should make this very clear in the `ChatOpenAI` documentation/source.

## Related PRs

#32982
#33836
#34049
#34705
#34747
#35067
#35180

- Proposing to add `reasoning_content` to `additional_kwargs` on `ChatOpenAI`

#34236

- Proposing to add `reasoning_content`/`reasoning` to `_convert_message_to_dict` and `_convert_dict_to_message` in `ChatOpenAI` for DeepSeek/OpenAI-compatible reasoning models

#34313

- Proposing to support OpenRouter's `reasoning_details` in `additional_kwargs` of `ChatOpenAI` to access structured reasoning metadata (tokens, steps, etc.)

#34347

- Proposing to handle streaming reasoning tokens in `ChatOpenAI` for DeepSeek-like models (complements #34236 for the streaming path)

#34362

- Proposing to add `reasoning_content` to `additional_kwargs` on `ChatOpenAI` for SiliconFlow

#34791

- Proposing to handle null for `choices` as returned by vLLM (related to `model_dump`)

#35027

- Proposing to preserve `reasoning_content` in `ChatOpenAI` specifically for DeepSeek models (both standard and streaming responses)

#35193

- Proposing a centralized `reasoning.py` module in `langchain-openai` that normalizes reasoning data from multiple field names (`reasoning_content`, `reasoning`, `thinking`) across providers. Updates all message conversion paths (`base.py`, `_compat.py`) for sync, async, and streaming.
- Some interesting stuff here going on with mapping provider-specific fields

## Implementations

#33902

- Add `ChatOpenRouter` by subclassing `BaseChatOpenAI`

#34867

- Add `ChatOpenRouter` by subclassing `BaseChatModel`

## TODO
We need to update the example in the OpenRouter / LiteLLM / vLLM docs.

## Unrelated but worth investigating

#31437

- `BaseOpenAI` passes internal default params (e.g., `frequency_penalty`) to all requests even when not specified by the user, unlike `BaseChatOpenAI` which omits unset optional params. This breaks OpenAI-compatible APIs that don't support all parameters.

#31657

- Tool-calling flows fail when using Anthropic models via OpenRouter with `ChatOpenAI`. A `SystemMessage` followed by `AIMessage`s and tool results causes a 400 error about unexpected `tool_use_id` in `tool_result` blocks — a message format mismatch between OpenAI and Anthropic conventions as translated by OpenRouter.

#32252

- User is attempting to access a Runpod endpoint that serves a vLLM model via `ChatOpenAI`
- It is unclear whether the Runpod vLLM API is actually OpenAI compatible
- Problem may be in `model_dump()`

#33672

- User wants `ChatOpenAI` to support extracting Qwen3's thinking/reasoning process (like it does for DeepSeek). `reasoning_content` is not captured. `ChatTongyi` doesn't allow custom `base_url` for local models. The official OpenAI SDK works fine for this.

#33834

- User is attempting to access models from Volcengine via `ChatOpenAI` for Doubao models (`doubao-seed-1-6-251015`)
  - Volcengine may support Responses API

#34011

- Reasoning content in Hugging Face responses
- Related PR: #34014

#34166

- Issues with `ChatDeepSeek` and `reasoning_content`

#34342

- `reasoning_content` purportedly not being captured in `ChatFireworks`

#34436

- I'm not sure. Something wrong with `reasoning_content` in `ChatDeepSeek`
  - Possibly related PR: #34092, #34177, #34438, #34516, #35094

#34446

- User claims `deepseek-r1` when not streaming lacks `reasoning_content`
  - Possibly related PR: #34092, #34177, #34438, #34516, #35094

#34933

- Switching from a provider with proprietary signature fields will potentially result in API errors

#35006

- User is attempting to call `deepseek-reasoner` via `ChatOpenAI`
- `ChatDeepSeek` has issues with `reasoning_content`
  - Possibly related PR: #34092, #34177, #34438, #34516, #35094

#35059

- User wants to access vLLM and DeepSeek, but `ChatOpenAI` doesn't capture `reasoning_content`. Switching to `ChatDeepSeek` resolves.

#34612

- Reasoning format for `ChatOllama`

#35188

- Handling `` tags for certain models in services building atop Chat Completions

## Comments

**xiangnuans:**
I’m happy to help move this forward.

For context, I recently worked on #34313, which added support for OpenRouter’s reasoning_details as provider-specific metadata (including streaming delta merging). While that change doesn’t belong in the OpenAI integration, the underlying approach should translate cleanly to a dedicated OpenRouter package.

Once the expected structure for the OpenRouter integration is clearer, I can help with a proposal or an initial implementation based on that work.

**Saryazdi-Saman:**
Thanks for creating this tracking issue! I was part of the discussion in #32982 where this issue came up. Happy to help with testing, reviewing, or the TypeScript implementation if needed. Just let me know how I can contribute!

**jingyugao:**
Hi, any update on this issue?

**ibbybuilds:**
following this

**ZainCheung:**
following this

**DevDeepakBhattarai:**
following this

**mkc-cho:**
following this! We need this to deliver our product.

**mhrlife:**
following this

**ibbybuilds:**
@xiangnuans hey, are you working on this? would love to help in any way possible.

**DevDeepakBhattarai:**
Actually, I got `ChatOpenRouter` for my usecase. Although its not a library yet. It does work and puts out the reasoning content (the entire things openrouter gives) in the `additional_kwargs`. @ibbybuilds I am trying to figure out how to populate `contentBlocks` with the reasoning data.  It would be great if you could help

```ts

/**
 * ChatOpenRouter - Extends ChatOpenAI with OpenRouter + reasoning support
 *
 * @requires @langchain/openai
 * @requires @langchain/core
 */

import { getEnvironmentVariable } from "@langchain/core/utils/env";
import {
  type ChatOpenAICallOptions,
  ChatOpenAICompletions,
  type ChatOpenAIFields,
  convertCompletionsDeltaToBaseMessageChunk,
  convertCompletionsMessageToBaseMessage,
  type OpenAIClient,
} from "@langchain/openai";

// ============================================================================
// TYPES
// ============================================================================

export interface OpenRouterReasoningConfig {
  effort?: "high" | "medium" | "low";
  max_tokens?: number;
  exclude?: boolean;
}

export interface OpenRouterProviderConfig {
  order?: string[];
  allow_fallbacks?: boolean;
  require_parameters?: boolean;
  only?: string[];
  ignore?: string[];
  data_collection?: "allow" | "deny";
  sort?: "throughput";
  quantizations?: string[];
}

/**
 * Reasoning detail types from OpenRouter responses
 */
export type ReasoningDetailFormat =
  | "unknown"
  | "openai-responses-v1"
  | "xai-responses-v1"
  | "anthropic-claude-v1";

export interface ReasoningDetailSummary {
  type: "reasoning.summary";
  summary: string;
  id?: string | null;
  format?: ReasoningDetailFormat;
  index?: number;
}

export interface ReasoningDetailEncrypted {
  type: "reasoning.encrypted";
  data: string;
  id?: string | null;
  format?: ReasoningDetailFormat;
  index?: number;
}

export interface ReasoningDetailText {
  type: "reasoning.text" | "thinking";
  text: string;
  signature?: string | null;
  id?: string | null;
  format?: ReasoningDetailFormat;
  index?: number;
}

export type ReasoningDetail =
  | ReasoningDetailSummary
  | ReasoningDetailEncrypted
  | ReasoningDetailText;

export interface ChatOpenRouterCallOptions extends ChatOpenAICallOptions {
  /** OpenRouter reasoning configuration */
  reasoning?: OpenRouterReasoningConfig;
  /** OpenRouter provider routing */
  provider?: OpenRouterProviderConfig;
  /** Extra headers for this request */
  headers?: Record;
}

export interface ChatOpenRouterInput
  extends Omit {
  /**
   * OpenRouter API key
   * @default process.env.OPENROUTER_API_KEY
   */
  apiKey?: string;
  /**
   * Model to use (e.g., "openai/gpt-4o", "anthropic/claude-sonnet-4", "deepseek/deepseek-r1")
   */
  model?: string;
  /**
   * Your site URL for OpenRouter rankings
   */
  siteUrl?: string;
  /**
   * Your site/app name for OpenRouter rankings
   */
  siteName?: string;
  /**
   * Default reasoning configuration
   */
  reasoning?: OpenRouterReasoningConfig;
  /**
   * Default provider routing configuration
   */
  provider?: OpenRouterProviderConfig;
}

// ============================================================================
// MAIN CLASS
// ============================================================================

/**
 * OpenRouter chat model - extends ChatOpenAI with reasoning support.
 *
 * OpenRouter provides access to 300+ models through a unified OpenAI-compatible API.
 * This class adds automatic reasoning extraction for thinking models like DeepSeek R1,
 * Claude with extended thinking, OpenAI o-series, etc.
 *
 * @example
 * ```typescript
 * import { ChatOpenRouter } from "./chat-openrouter";
 *
 * // Basic usage - same as ChatOpenAI
 * const llm = new ChatOpenRouter({
 *   model: "openai/gpt-4o",
 * });
 *
 * // With reasoning model
 * const reasoningLlm = new ChatOpenRouter({
 *   model: "deepseek/deepseek-r1",
 *   reasoning: { effort: "high" },
 * });
 *
 * const response = await reasoningLlm.invoke("Which is larger: 9.11 or 9.9?");
 * console.log(response.content); // The answer
 * console.log(response.additional_kwargs.reasoning_content); // The thinking
 * ```
 */
export class ChatOpenRouter extends ChatOpenAICompletions {
  static lc_name() {
    return "ChatOpenRouter";
  }

  _llmType() {
    return "openrouter";
  }

  get lc_secrets(): { [key: string]: string } | undefined {
    return {
      apiKey: "OPENROUTER_API_KEY",
      openAIApiKey: "OPENROUTER_API_KEY",
    };
  }

  lc_serializable = true;

  // OpenRouter-specific fields
  reasoning?: OpenRouterReasoningConfig;
  provider?: OpenRouterProviderConfig;
  siteUrl?: string;
  siteName?: string;

  constructor(fields?: ChatOpenRouterInput) {
    const apiKey =
      fields?.apiKey ?? getEnvironmentVariable("OPENROUTER_API_KEY");

    if (!apiKey) {
      throw new Error(
        `OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable or pass apiKey.`,
      );
    }

    // Build default headers for OpenRouter
    const defaultHeaders: Record = {};
    if (fields?.siteUrl) {
      defaultHeaders["HTTP-Referer"] = fields.siteUrl;
    }
    if (fields?.siteName) {
      defaultHeaders["X-Title"] = fields.siteName;
    }

    super({
      ...fields,
      openAIApiKey: apiKey,
      configuration: {
        baseURL: "https://openrouter.ai/api/v1",
        defaultHeaders:
          Object.keys(defaultHeaders).length > 0 ? defaultHeaders : undefined,
      },
    });

    this.reasoning = fields?.reasoning;
    this.provider = fields?.provider;
    this.siteUrl = fields?.siteUrl;
    this.siteName = fields?.siteName;
  }

  /**
   * Override to inject reasoning and provider params into the request
   */
  override invocationParams(
    options?: this["ParsedCallOptions"],
  ): Omit {
    const params = super.invocationParams(options);

    // Add reasoning config
    const reasoning = options?.reasoning ?? this.reasoning;
    if (reasoning) {
      (params as Record).reasoning = reasoning;
    }

    // Add provider config
    const provider = options?.provider ?? this.provider;
    if (provider) {
      (params as Record).provider = provider;
    }

    return params;
  }

  /**
   * Extract reasoning_content from streaming delta
   */
  protected override _convertCompletionsDeltaToBaseMessageChunk(
    // biome-ignore lint/suspicious/noExplicitAny: Type later
    delta: Record,
    rawResponse: OpenAIClient.ChatCompletionChunk,
    defaultRole?:
      | "function"
      | "user"
      | "system"
      | "developer"
      | "assistant"
      | "tool",
  ) {
    const messageChunk = convertCompletionsDeltaToBaseMessageChunk({
      delta,
      rawResponse,
      defaultRole,
    });
    // Extract reasoning_details (Claude, OpenAI o-series style)
    if (delta.reasoning_details) {
      // Store the raw reasoning_details for passing back to models
      const existingDetails =
        (messageChunk.additional_kwargs
          .reasoning_details as ReasoningDetail[]) ?? [];
      messageChunk.additional_kwargs.reasoning_details = [
        ...existingDetails,
        ...delta.reasoning_details,
      ] as ReasoningDetail[];
    }

    return messageChunk;
  }

  /**
   * Extract reasoning_details from non-streaming response
   */
  protected override _convertCompletionsMessageToBaseMessage(
    message: OpenAIClient.ChatCompletionMessage,
    rawResponse: OpenAIClient.ChatCompletion,
  ) {
    const langChainMessage = convertCompletionsMessageToBaseMessage({
      message,
      rawResponse,
    });

    // biome-ignore lint/suspicious/noExplicitAny: OpenRouter extends the standard type
    const msg = message as any;

    // Extract reasoning_details (Claude, OpenAI o-series style)
    if (msg.reasoning_details) {
      // Store the raw reasoning_details for passing back to models
      langChainMessage.additional_kwargs.reasoning_details =
        msg.reasoning_details as ReasoningDetail[];
    }

    return langChainMessage;
  }
}

export default ChatOpenRouter;

```

Here is my code for `ChatOpenRouter` 

PS: This is the TS version. But I think the implementation should be same to populate the `contentBlocks`
