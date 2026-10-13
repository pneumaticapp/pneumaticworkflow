import { DatePickerProps } from 'react-datepicker';

type TSingleLibraryProps = Extract<DatePickerProps, { selectsMultiple?: never; selectsRange?: never }>;
type TRangeLibraryProps = Extract<DatePickerProps, { selectsRange: true }>;

type TOmittedLibraryProps =
  | 'onChange'
  | 'selected'
  | 'startDate'
  | 'endDate'
  | 'selectsRange'
  | 'showTimeInput'
  | 'showTimeSelect'
  | 'showTimeSelectOnly'
  | 'timeIntervals'
  | 'timeCaption'
  | 'timeFormat'
  | 'timeInputLabel';

type TSharedSingleProps = Omit<TSingleLibraryProps, TOmittedLibraryProps>;
type TSharedRangeProps = Omit<TRangeLibraryProps, TOmittedLibraryProps>;

export interface ISingleDatePickerProps extends TSharedSingleProps {
  selectsRange?: false;
  startDay?: true;
  selected?: Date | null;
  /** When false, parent owns clear UI (e.g. trailing DateIcon slot). Default true. */
  isClearable?: boolean;
  onChange(date: Date | null): void;
}

export interface IRangeDatePickerProps extends TSharedRangeProps {
  selectsRange: true;
  startDate?: Date | null;
  endDate?: Date | null;
  /** When false, parent owns clear UI. Default true. */
  isClearable?: boolean;
  onChange(dates: [Date | null, Date | null]): void;
}

export type IDatePickerProps = ISingleDatePickerProps | IRangeDatePickerProps;

export const isRangeDatePickerProps = (props: IDatePickerProps): props is IRangeDatePickerProps => {
  return props.selectsRange === true;
};
