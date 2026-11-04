import { connect } from 'react-redux';

import { DateFormatComponent, IDateFormatProps } from './DateFormat';
import type { IApplicationState } from '../../../redux/store';

type TStoreProps = Pick<IDateFormatProps, 'dateFmt' | 'timezone' | 'language'>;

const mapStateToProps = ({ authUser: { dateFmt, timezone, language } }: IApplicationState): TStoreProps => {
  return { dateFmt, timezone, language };
};

export const DateFormat = connect(mapStateToProps)(DateFormatComponent);
