import type { ICreateUserRequest } from '../../../../types/user';

export interface ICreatePerformerModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: ECreatePerformerModalTab;
}

export enum ECreatePerformerModalTab {
  User = 'user',
  AIAgent = 'ai-agent',
}

export const enum EUserRole {
  Admin = 'Admin',
  User = 'User',
}

export interface IStatusOption {
  label: string;
  value: EUserRole;
}

export interface ICreateUserFormValues extends Required<
  Pick<ICreateUserRequest, 'firstName' | 'lastName' | 'email' | 'password'>
> {
  role: EUserRole;
}

export interface ICreateUserFormProps {
  isActive: boolean;
  isOpen: boolean;
}

export interface IAIAgentFormValues {
  name: string;
  providerId: string;
  model: string;
  systemPrompt: string;
  photo: string;
}

export interface IAIAgentFormProps {
  isActive: boolean;
  isOpen: boolean;
  isSubmitting?: boolean;
  initialValues?: IAIAgentFormValues;
  submitLabel: string;
  onSubmit(values: IAIAgentFormValues): void;
}
