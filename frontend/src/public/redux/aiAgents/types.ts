export interface IAiAgent {
  id: number;
  name: string;
  modelSlug: string;
  systemPrompt: string;
  temperature: number | null;
  maxTokens: number | null;
  photo: string | null;
  isActive: boolean;
}

export type TAiAgentDraft = Omit<IAiAgent, 'id'>;

export interface IAiConnection {
  id: number;
  baseUrl: string;
  apiKeyMask: string;
}

export type TAiConnectionDraft = {
  apiKey: string;
  baseUrl?: string;
};
