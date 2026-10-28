import type { IAIAgent, IAIModel, IAIProvider, IAIVendor, TUpdateAIAgentRequest } from '../../api/ai/types';

export interface IAIStore {
  providers: {
    isLoading: boolean;
    list: IAIProvider[];
  };
  createProviderModal: {
    isOpen: boolean;
    isLoading: boolean;
  };
  agents: {
    isLoading: boolean;
    list: IAIAgent[];
  };
  vendors: {
    isLoading: boolean;
    list: IAIVendor[];
  };
  models: {
    isLoading: boolean;
    providerId: number | null;
    list: IAIModel[];
  };
}

export type TUpdateAIAgentPayload = { id: number; onSuccess?(): void; onError?(): void } & TUpdateAIAgentRequest;

export interface IUploadAIAgentAvatarPayload {
  file: File;
  onSuccess(url: string): void;
}
