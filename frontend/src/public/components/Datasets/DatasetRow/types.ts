export interface IDatasetRowProps {
  value?: string;
  isEditing?: boolean;
  existingItems?: string[];
  onEdit?(): void;
  onCancel?(): void;
  onSave(value: string): void;
  onDelete(): void;
}
