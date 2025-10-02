import { connect } from 'react-redux';
import { Dashboard, IDashboardProps } from './Dashboard';
import { EDashboardModes, IApplicationState } from '../../types/redux';
import {
  loadDashboardData,
  setDashboardTimeRange,
  resetDashboardData,
  openSelectTemplateModal,
  loadBreakdownTasks,
  setDashboardMode,
  openRunWorkflowModalByTemplateId,
} from '../../redux/actions';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { EDashboardTimeRange } from '../../types/dashboard';
import { getIsUserSubsribed } from '../../redux/selectors/user';

type TDashboardStoreProps = Pick<IDashboardProps,
| 'isLoading'
| 'counters'
| 'isVerified'
| 'timeRange'
| 'isSubscribed'
| 'dashboardMode'
| 'settingsChanged'
| 'breakdownItems'
>;
type TDashboardDispatchProps = Pick<IDashboardProps,
| 'loadDashboardData'
| 'resetDashboardData'
| 'openSelectTemplateModal'
| 'loadBreakdownTasks'
| 'setDashboardMode'
| 'openRunWorkflowModalOnDashboard'
>;

export function mapStateToProps(state: IApplicationState): TDashboardStoreProps {
  const { authUser, dashboard } = state;
  const isSubscribed = getIsUserSubsribed(state);

  return {
    isLoading: dashboard.isLoading,
    counters: dashboard.counters,
    isVerified: authUser.account.isVerified,
    timeRange: dashboard.timeRange,
    isSubscribed,
    dashboardMode: authUser.isAdmin ? dashboard.mode : EDashboardModes.Tasks,
    settingsChanged: dashboard.settingsChanged,
    breakdownItems: dashboard.breakdownItems,
  };
}

export const mapDispatchToProps: TDashboardDispatchProps = {
  loadDashboardData,
  resetDashboardData,
  openSelectTemplateModal,
  loadBreakdownTasks,
  setDashboardMode,
  openRunWorkflowModalOnDashboard: openRunWorkflowModalByTemplateId,
};

const SyncedDashboard = withSyncedQueryString<IDashboardProps>([{
  propName: 'timeRange',
  queryParamName: 'time-range',
  defaultAction: setDashboardTimeRange(EDashboardTimeRange.Today),
  createAction: setDashboardTimeRange,
  getQueryParamByProp: value => value,
}])(Dashboard);

export const DashboardContainer = connect<
TDashboardStoreProps,
TDashboardDispatchProps
>(mapStateToProps, mapDispatchToProps)(SyncedDashboard);
