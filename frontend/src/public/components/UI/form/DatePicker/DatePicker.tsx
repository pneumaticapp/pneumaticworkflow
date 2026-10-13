import React from 'react';

import { RangeDatePicker, SingleDatePicker } from './components';
import { IDatePickerProps, isRangeDatePickerProps } from './types';

import 'react-datepicker/dist/react-datepicker.css';
import '../../../../assets/css/library/react-datepicker.css';

export function DatePickerCustom(props: IDatePickerProps) {
  if (isRangeDatePickerProps(props)) {
    return <RangeDatePicker {...props} />;
  }

  return <SingleDatePicker {...props} />;
}
