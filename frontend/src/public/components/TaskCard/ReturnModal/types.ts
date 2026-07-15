export interface IReturnModalProps {
  isOpen: boolean;
  isConfirmDisabled?: boolean;
  onClose(): void;
  onConfirm(message: string): void;
}
