import type { ChangeEvent, FormEvent } from 'react';
import type { IApiKeyItem } from '../../../types/integrations';

export interface IApiKeyListItemProps {
  apiKey: IApiKeyItem;
  onRevoke: (id: number) => void;
}

export interface ICreateApiKeyModalProps {
  isOpen: boolean;
  name: string;
  onNameChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onClose: () => void;
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
