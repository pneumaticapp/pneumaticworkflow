export interface IDueInProps {
  dueDate: string | null;
  timezone: string;
  dateFmt: string;
  showIcon?: boolean;
  containerClassName?: string;
  view?: 'timeLeft' | 'dueDate';
  withTime?: boolean;
  onSave(date: string): void;
  onRemove(): void;
  dateCompleted: string | null;
}