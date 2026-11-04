import { connect } from 'react-redux';

import { DateFormatComponent, IDateFormatProps } from './DateFormat';
import type { RootState } from '../../../redux/store';

type TStoreProps = Pick<IDateFormatProps, 'dateFmt' | 'timezone' | 'language'>;

const mapStateToProps = ({ authUser: { dateFmt, timezone, language } }: RootState): TStoreProps => {
  return { dateFmt, timezone, language };
};

export const DateFormat = connect(mapStateToProps)(DateFormatComponent);
