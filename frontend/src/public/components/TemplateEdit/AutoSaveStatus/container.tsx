import { connect } from 'react-redux';

import type { IAutoSaveStatusProps } from './AutoSaveStatus';
import { AutoSaveStatus } from './AutoSaveStatus';

import type { RootState } from '../../../redux/store';
import { getPaywallType } from '../../TopNav/utils/getPaywallType';

type TStoreProps = Pick<IAutoSaveStatusProps, 'templateStatus' | 'withPaywall'>;

export function mapStateToProps({
  template: { status: templateStatus },
  authUser: {
    account: { billingPlan, isBlocked },
  },
}: RootState): TStoreProps {
  const withPaywall = Boolean(getPaywallType(billingPlan, isBlocked));

  return { templateStatus, withPaywall };
}

export const AutoSaveStatusContainer = connect(mapStateToProps)(AutoSaveStatus);
