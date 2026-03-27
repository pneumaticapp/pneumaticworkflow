export interface IDatasetRowProps {
  value?: string;
  isEditing?: boolean;
  onCancel?(): void;
  onSave(value: string): void;
  onDelete(): void;
}
