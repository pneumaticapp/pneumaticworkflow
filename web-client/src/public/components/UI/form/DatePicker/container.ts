import { connect } from 'react-redux';

import { IApplicationState } from '../../../../types/redux';
import { DatePickerComponent, IDatePickerProps } from './DatePicker';

type TStoreProps = Pick<IDatePickerProps, 'dateFdw' | 'language' | 'timezone'>;

function mapStateToProps({
  authUser: { dateFdw, language, timezone }
}: IApplicationState): TStoreProps {
  return {
    dateFdw,
    language,
    timezone
  };
}

export const DatePicker = connect(mapStateToProps)(DatePickerComponent);
