import type { IAIAgent, IAIModel, IAIProvider, IAIVendor } from '../../api/ai/types';

export interface IAIStore {
  providers: {
    isLoading: boolean;
    list: IAIProvider[];
  };
  createProvider: {
    status: 'idle' | 'pending' | 'succeeded' | 'failed';
    requestId: number | null;
  };
  createAgent: {
    status: 'idle' | 'pending' | 'succeeded' | 'failed';
    requestId: number | null;
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
  isSaving: boolean;
}
