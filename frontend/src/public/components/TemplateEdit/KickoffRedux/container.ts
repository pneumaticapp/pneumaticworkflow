import { connect } from 'react-redux';
import { injectIntl } from 'react-intl';

import { IApplicationState } from '../../../types/redux';

import { IKickoffReduxProps, KickoffRedux } from './KickoffRedux';

type TStoreProps = Pick<IKickoffReduxProps, 'accountId'>;

export function mapStateToProps({
  authUser: { account },
}: IApplicationState): TStoreProps {
  return {
    accountId: account.id || -1,
  };
}

export const KickoffReduxContainer = injectIntl(connect<TStoreProps>(mapStateToProps)(KickoffRedux));
