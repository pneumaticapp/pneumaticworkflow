/* prettier-ignore */
import { connect } from 'react-redux';
import type { IApplicationState } from '../../redux/store';

import { EditKickoff, IEditKickoffProps } from './KickoffEdit';

type TStoreProps = Pick<IEditKickoffProps, 'accountId'>;

const mapStateToProps = ({ authUser: { account } }: IApplicationState): TStoreProps => {
  return { accountId: account.id || -1 };
};

export const EditKickoffContainer = connect(mapStateToProps)(EditKickoff);
