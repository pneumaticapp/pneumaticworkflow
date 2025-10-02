import { connect } from 'react-redux';

import { DateFormatComponent, IDateFormatProps } from './DateFormat';
import { IApplicationState } from '../../../types/redux';

type TStoreProps = Pick<IDateFormatProps, 'dateFmt' | 'timezone' | 'language'>;

const mapStateToProps = (
  { authUser: { dateFmt, timezone, language } }: IApplicationState,
): TStoreProps => {
  return { dateFmt, timezone, language };
};

export const DateFormat = connect(mapStateToProps)(DateFormatComponent);
