import type { IAIProvider } from '../../../api/ai/types';

export interface IAIProviderListItemProps {
  provider: IAIProvider;
  onDelete: (id: number) => void;
}

export interface ICreateAIProviderModalProps {
  isOpen: boolean;
  onClose(): void;
}

export interface ICreateAIProviderFormValues {
  vendor: string;
  name: string;
  baseUrl: string;
  apiKey: string;
}
