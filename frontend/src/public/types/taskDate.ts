export type TaskWithDateFields = {
  dueDate: string | null;
  dateStarted: string;
  dateCompleted: string | null;
};

export type TaskWithTspFields = {
  dueDateTsp: number | null;
  dateStartedTsp: number;
  dateCompletedTsp: number | null;
};

export type TaskWithTsp<T> = Omit<T, keyof TaskWithDateFields> & TaskWithTspFields;
