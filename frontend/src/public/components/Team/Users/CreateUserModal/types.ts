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
