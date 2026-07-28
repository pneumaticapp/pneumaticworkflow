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
