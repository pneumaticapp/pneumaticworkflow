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
