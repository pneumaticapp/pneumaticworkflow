/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';

import { EditKickoff, IEditKickoffProps } from './KickoffEdit';

type TStoreProps = Pick<IEditKickoffProps, 'accountId'>;

const mapStateToProps = (
  {
    authUser: { account },
  }: IApplicationState,
): TStoreProps => {

  return { accountId: account.id || -1 };
};

export const EditKickoffContainer = connect(mapStateToProps)(EditKickoff);
