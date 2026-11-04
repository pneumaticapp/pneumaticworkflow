import { connect } from 'react-redux';
import { injectIntl } from 'react-intl';

import type { RootState } from '../../../redux/store';

import { IKickoffReduxProps, KickoffRedux } from './KickoffRedux';

type TStoreProps = Pick<IKickoffReduxProps, 'template' | 'accountId' | 'templateStatus'>;

export function mapStateToProps({
  template: { data: template, status },
  authUser: { account },
}: RootState): TStoreProps {
  return {
    template,
    templateStatus: status,
    accountId: account.id || -1,
  };
}

export const KickoffReduxContainer = injectIntl(connect(mapStateToProps)(KickoffRedux));
