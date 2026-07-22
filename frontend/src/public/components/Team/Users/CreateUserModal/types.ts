import { ICreateUserRequest } from '../../../../types/user';

export interface ICreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateAIAgent?(values: ICreateAIAgentFormValues): void;
}

export enum ECreateUserModalTab {
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

export interface ICreateUserFormValues extends Required<Pick<ICreateUserRequest, 'firstName' | 'lastName' | 'email' | 'password'>> {
  role: EUserRole;
}

export interface ICreateAIAgentFormValues {
  firstName: string;
  lastName: string;
  position: string;
  model: string;
  endpoint: string;
  apiKey: string;
  systemPrompt: string;
  avatar: string;
}

export interface ICreateAIAgentFormProps {
  isActive: boolean;
  isOpen: boolean;
  onSubmit(values: ICreateAIAgentFormValues): void;
}