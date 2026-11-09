import React from 'react';
import { useIntl } from 'react-intl';

import { RangeDatePicker, SingleDatePicker } from './components';
import { IDatePickerProps, isRangeDatePickerProps } from './types';

import 'react-datepicker/dist/react-datepicker.css';
import '../../../../assets/css/library/react-datepicker.css';

export function DatePickerCustom(props: IDatePickerProps) {
  const { formatMessage } = useIntl();
  const previousMonth = formatMessage({ id: 'ui.date.previous-month' });
  const nextMonth = formatMessage({ id: 'ui.date.next-month' });
  const previousYear = formatMessage({ id: 'ui.date.previous-year' });
  const nextYear = formatMessage({ id: 'ui.date.next-year' });
  const accessibilityProps = {
    previousMonthAriaLabel: previousMonth,
    previousMonthButtonLabel: previousMonth,
    nextMonthAriaLabel: nextMonth,
    nextMonthButtonLabel: nextMonth,
    previousYearAriaLabel: previousYear,
    previousYearButtonLabel: previousYear,
    nextYearAriaLabel: nextYear,
    nextYearButtonLabel: nextYear,
    chooseDayAriaLabelPrefix: formatMessage({ id: 'ui.date.choose-day' }),
    disabledDayAriaLabelPrefix: formatMessage({ id: 'ui.date.unavailable-day' }),
    monthAriaLabelPrefix: formatMessage({ id: 'ui.date.month' }),
    timeCaption: formatMessage({ id: 'due-date.time' }),
  };
  if (isRangeDatePickerProps(props)) {
    return <RangeDatePicker popperPlacement="bottom-start" {...accessibilityProps} {...props} />;
  }

  return <SingleDatePicker popperPlacement="bottom-start" {...accessibilityProps} {...props} />;
}
