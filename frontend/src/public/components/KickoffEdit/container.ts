/* prettier-ignore */
import { connect } from 'react-redux';
import type { RootState } from '../../redux/store';

import type { IEditKickoffProps } from './KickoffEdit';
import { EditKickoff } from './KickoffEdit';

type TStoreProps = Pick<IEditKickoffProps, 'accountId'>;

const mapStateToProps = ({ authUser: { account } }: RootState): TStoreProps => {
  return { accountId: account.id || -1 };
};

export const EditKickoffContainer = connect(mapStateToProps)(EditKickoff);
