import type { IAIProvider } from '../../../api/ai/types';

export interface IAIProviderListItemProps {
  provider: IAIProvider;
  onDelete: (id: number) => void;
}

export interface ICreateAIProviderFormValues {
  vendor: string;
  name: string;
  baseUrl: string;
  apiKey: string;
}

export enum ECreateAIProviderTab {
  Vendor = 'vendor',
  Custom = 'custom',
}
