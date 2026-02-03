export interface ICreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export type TUserStatus = 'Admin' | 'User';

export interface ICreateUserFormData {
  firstName: string;
  lastName: string;
  email: string;
  status: TUserStatus;
  password: string;
}

export interface IStatusOption {
  label: string;
  value: TUserStatus;
}
