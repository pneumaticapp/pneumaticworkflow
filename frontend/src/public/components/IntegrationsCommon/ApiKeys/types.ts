import type { IApiKeyItem } from '../../../types/integrations';

export interface IApiKeyListItemProps {
  apiKey: IApiKeyItem;
  onRevoke: (id: number) => void;
}

export interface ICreateApiKeyModalProps {
  isOpen: boolean;
  onSubmit: (name: string) => void;
  onClose: () => void;
}

export interface ICreateApiKeyFormValues {
  name: string;
}

export interface INewApiKeyModalProps {
  apiKey: string | null;
  onClose: () => void;
  onCopy: () => void;
}

export interface IRevokeApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}
