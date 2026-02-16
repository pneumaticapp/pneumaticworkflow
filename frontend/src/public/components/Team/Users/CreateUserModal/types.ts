import { ICreateUserRequest } from '../../../../types/user';

export interface ICreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
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