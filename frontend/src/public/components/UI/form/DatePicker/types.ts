import { DatePickerProps } from 'react-datepicker';

export type IDatePickerProps = Omit<DatePickerProps, 'onChange'> & {
  startDay?: true;
  onChange(date: Date | null): void;
};
