/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { compose } from 'redux';
import { injectIntl } from 'react-intl';

import { IApplicationState } from '../../types/redux';
import { resendVerification } from '../../redux/auth/actions';
import { setDashboardTimeRange, setDashboardMode, setDashboardSettingsManuallyChanged } from '../../redux/dashboard/actions';
import {
  IDashboardLayoutStoreProps,
  IDashboardLayoutDispatchProps,
  DashboardLayoutComponent,
} from './DashboardLayout';

const mapStateToProps = ({
  dashboard: { timeRange: currentTimeRange, mode: dashboardMode },
  authUser: { account: { isVerified }, isAdmin, isAccountOwner },
}: IApplicationState): IDashboardLayoutStoreProps => {
  return {
    isVerified,
    currentTimeRange,
    dashboardMode,
    isAdmin,
    isAccountOwner,
  };
};

const mapDispatchToProps: IDashboardLayoutDispatchProps = {
  resendVerification,
  setTimeRange: setDashboardTimeRange,
  setDashboardMode,
  setDashboardSettingsManuallyChanged,
};

export const DashboardLayoutContainer = compose(
  connect<IDashboardLayoutStoreProps, IDashboardLayoutDispatchProps>(mapStateToProps, mapDispatchToProps),
  injectIntl,
)(DashboardLayoutComponent);
