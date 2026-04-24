import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';

import { TopNavContainer } from '../../components/TopNav';
import { EDashboardTimeRange } from '../../types/dashboard';
import { EDashboardModes, IApplicationState } from '../../types/redux';
import { SelectMenu, Tabs } from '../../components/UI';
import { FilterIcon } from '../../components/icons';
import { getCanAccessWorkflows } from '../../redux/selectors/user';
import {
  setDashboardTimeRange,
  setDashboardMode,
  setDashboardSettingsManuallyChanged,
} from '../../redux/dashboard/actions';

import styles from './DashboardLayout.css';

const timeRangesTitles = Object.values(EDashboardTimeRange);
const dashboardModesEnum = Object.values(EDashboardModes);

export const DashboardLayoutComponent: React.FC = ({ children }) => {
  const intl = useIntl();
  const dispatch = useDispatch();

  const currentTimeRange = useSelector((state: IApplicationState) => state.dashboard.timeRange);
  const dashboardMode = useSelector((state: IApplicationState) => state.dashboard.mode);
  const canAccessWorkflows = useSelector(getCanAccessWorkflows);

  const dashboardModes = React.useMemo(
    () =>
      dashboardModesEnum.map((mode) => ({
        id: mode,
        label: intl.formatMessage({ id: mode }),
      })),
    [intl]
  );

  const handleSetTimeRange = React.useCallback(
    (newTimeRange: EDashboardTimeRange) => {
      dispatch(setDashboardSettingsManuallyChanged());
      dispatch(setDashboardTimeRange(newTimeRange));
    },
    [dispatch]
  );

  const handleSetDashboardMode = React.useCallback(
    (newDashboardMode: EDashboardModes) => {
      dispatch(setDashboardMode(newDashboardMode));
    },
    [dispatch]
  );

  const leftContent = (
    <div className={styles['navbar-left__content']}>
      <div className={styles['filters']}>
        {canAccessWorkflows && (
          <Tabs values={dashboardModes} activeValueId={dashboardMode} onChange={handleSetDashboardMode} />
        )}
        <SelectMenu
          values={timeRangesTitles}
          activeValue={currentTimeRange}
          onChange={handleSetTimeRange}
          Icon={FilterIcon}
        />
      </div>
    </div>
  );

  return (
    <>
      <TopNavContainer leftContent={leftContent} />
      <main className={styles['main']}>
        <div className="container-fluid">{children}</div>
      </main>
    </>
  );
};
