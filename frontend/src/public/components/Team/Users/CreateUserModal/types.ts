import { ICreateUserRequest } from '../../../../types/user';

export interface ICreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Tab shown on open; the Team AI Agents page opens straight on the agent form. */
  initialTab?: ECreateUserModalTab;
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

/**
 * Mirrors the AIAgent API contract: the provider credentials live on the provider
 * (Integrations page), the agent only references it by id and picks a model slug.
 */
export interface IAIAgentFormValues {
  name: string;
  /** Stringified provider id — dropdown values are strings; '' means not selected. */
  providerId: string;
  /** Model slug from GET /ai/providers/:id/models. */
  model: string;
  systemPrompt: string;
  /** Hosted avatar URL; '' renders initials. */
  photo: string;
}

export interface IAIAgentFormProps {
  isActive: boolean;
  isOpen: boolean;
  initialValues?: IAIAgentFormValues;
  submitLabel: string;
  onSubmit(values: IAIAgentFormValues): void;
}