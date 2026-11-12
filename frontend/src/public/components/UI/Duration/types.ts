export interface IDurationProps {
  duration: string | null;
  durationMonths?: number | null;
  onEditDuration(duration: string): void;
  onEditDurationMonths?(months: number): void;
  dueDateDuration?: boolean;
}

export enum EDurationFieldType {
  Hour = 'hours',
  Day = 'days',
  Minute = 'minutes',
}
