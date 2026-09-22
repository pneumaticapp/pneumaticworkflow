/** Vendor codes the backend detects from the provider host (see AIVendor.CODE_BY_HOST). */
export enum EAIVendor {
  OpenAI = 'openai',
  OpenRouter = 'openrouter',
  Anthropic = 'anthropic',
  Gemini = 'gemini',
  Groq = 'groq',
  XAI = 'xai',
  AzureOpenAI = 'azure_openai',
  Together = 'together',
  Fireworks = 'fireworks',
  DeepSeek = 'deepseek',
  Mistral = 'mistral',
  Cerebras = 'cerebras',
  Perplexity = 'perplexity',
  HuggingFace = 'huggingface',
  SambaNova = 'sambanova',
  NvidiaNim = 'nvidia_nim',
  OpenAICompatible = 'openai_compatible',
}

/** An agent that references the provider. Returned in AIProvider.usage, blocks deletion when non-empty. */
export interface IAIProviderUsageItem {
  id: number;
  name: string;
}

export interface IAIProvider {
  id: number;
  /** Read-only: derived by the backend from the base URL host. */
  name: string;
  baseUrl: string;
  /** Read-only masked prefix; the key itself is write-only and never returned. */
  apiKeyPrefix: string;
  /** Read-only: detected by the backend. */
  vendor: EAIVendor;
  isActive: boolean;
  usage: IAIProviderUsageItem[];
}

export interface ICreateAIProviderRequest {
  name: string;
  baseUrl: string;
  apiKey: string;
  isActive?: boolean;
}

export interface ICreateAIProviderByVendorRequest {
  vendor: string;
  apiKey: string;
}

export interface IAIVendor {
  slug: string;
  name: string;
}

export type TUpdateAIProviderRequest = Partial<ICreateAIProviderRequest>;

export interface IAIModel {
  name: string;
  slug: string;
}

export interface IAIAgent {
  id: number;
  name: string;
  photo: string | null;
  isActive: boolean;
  providerId: number;
  /** OpenRouter-style slug, taken from IAIModel.slug. */
  model: string;
  systemPrompt: string;
}

export interface ICreateAIAgentRequest {
  name: string;
  providerId: number;
  model: string;
  systemPrompt: string;
  isActive: boolean;
  photo?: string | null;
}

export type TUpdateAIAgentRequest = Partial<ICreateAIAgentRequest>;
