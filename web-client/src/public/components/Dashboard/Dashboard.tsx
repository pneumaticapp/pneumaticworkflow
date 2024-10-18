/* eslint-disable jsx-a11y/mouse-events-have-key-events */
/* eslint-disable react/destructuring-assignment */
import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { history } from '../../utils/history';

import { IDashboardCounterProps } from './Counters';
import { IDashboardCounters, EDashboardModes, TDashboardBreakdownItem } from '../../types/redux';
import { EDashboardTimeRange } from '../../types/dashboard';
import { DashboardCounters } from './Counters/DashboardCounters';
import { IntlMessages } from '../IntlMessages';
import { Header } from '../UI/Typeography/Header';
import { FilledInfoIcon } from '../icons';
import { CustomTooltip, ETooltipPlacement } from '../UI/CustomTooltip';
import { Breakdowns } from './Breakdowns';
import { Loader } from '../UI';
import { ILoadBreakdownTasksPayload, IOpenRunWorkflowPayload } from '../../redux/actions';
import { EDashboardCounterType } from './Counters/types';
import { getLinkToTasks } from '../../utils/routes/getLinkToTasks';
import { getLinkToWorkflows } from '../../utils/routes/getLinkToWorkflows';
import { ETaskListCompletionStatus, ETaskListSorting } from '../../types/tasks';
import { EWorkflowsSorting, EWorkflowsStatus } from '../../types/workflow';
import { DashboardWidgets } from './DashboardWidgets';

import styles from './Dashboard.css';

export interface IDashboardProps {
  isLoading?: boolean;
  counters: IDashboardCounters;
  isVerified?: boolean;
  timeRange: EDashboardTimeRange;
  isSubscribed: boolean;
  dashboardMode: EDashboardModes;
  settingsChanged: boolean;
  breakdownItems: TDashboardBreakdownItem[];
  loadDashboardData(): void;
  resetDashboardData(): void;
  openSelectTemplateModal(): void;
  loadBreakdownTasks(payload: ILoadBreakdownTasksPayload): void;
  setDashboardMode(payload: EDashboardModes): void;
  openRunWorkflowModalOnDashboard(payload: IOpenRunWorkflowPayload): void;
}

const { useRef, useState, useEffect, useCallback } = React;

export const Dashboard = (props: IDashboardProps) => {
  const { formatMessage } = useIntl();

  useEffect(() => {
    return () => props.resetDashboardData();
  }, []);

  useEffect(() => {
    props.loadDashboardData();
  }, [props.timeRange, props.dashboardMode]);

  useEffect(() => {
    const urlSearchParams = new URLSearchParams(history.location.search);
    if (urlSearchParams.get('page') === 'tasks') {
      props.setDashboardMode(EDashboardModes.Tasks);
    }
  }, []);

  const activitiesTitle = props.dashboardMode === EDashboardModes.Tasks ? 'tasks.title' : 'workflows.title';

  useEffect(() => {
    const urlSearchParams = new URLSearchParams(history.location.search);
    urlSearchParams.set('page', props.dashboardMode === EDashboardModes.Tasks ? 'tasks' : 'workflows');
    history.push({
      search: urlSearchParams.toString(),
    });
  }, [props.dashboardMode]);

  const tooltipIconRef = useRef<HTMLDivElement>(null);

  const [isTooltipShown, setIsTooltipShown] = useState(false);

  const getRoute = useCallback(
    (counterType: EDashboardCounterType) => {
      const tasksRouteMap = {
        [EDashboardCounterType.Started]: getLinkToTasks({ status: ETaskListCompletionStatus.Active }),
        [EDashboardCounterType.InProgress]: getLinkToTasks({ status: ETaskListCompletionStatus.Active }),
        [EDashboardCounterType.Overdue]: getLinkToTasks({ sorting: ETaskListSorting.Overdue }),
        [EDashboardCounterType.Completed]: getLinkToTasks({ status: ETaskListCompletionStatus.Completed }),
      };

      const workflowsRouteMap = {
        [EDashboardCounterType.Started]: getLinkToWorkflows({
          status: EWorkflowsStatus.Running,
        }),
        [EDashboardCounterType.InProgress]: getLinkToWorkflows({
          status: EWorkflowsStatus.Running,
        }),
        [EDashboardCounterType.Overdue]: getLinkToWorkflows({
          status: EWorkflowsStatus.Running,
          sorting: EWorkflowsSorting.Overdue,
        }),
        [EDashboardCounterType.Completed]: getLinkToWorkflows({
          status: EWorkflowsStatus.Completed,
        }),
      };

      const routeMap = {
        [EDashboardModes.Workflows]: workflowsRouteMap,
        [EDashboardModes.Tasks]: tasksRouteMap,
      };

      return routeMap[props.dashboardMode][counterType];
    },
    [props.dashboardMode],
  );

  const countersParamsList: () => IDashboardCounterProps[] = () => {
    const { counters } = props;

    return [
      {
        count: counters.started,
        label: formatMessage({ id: 'dashboard.counter-launched' }) as string,
        route: getRoute(EDashboardCounterType.Started),
        color: 'blue',
        className: styles['header-counter'],
      },
      {
        count: counters.inProgress,
        label: formatMessage({ id: 'dashboard.counter-ongoing' }) as string,
        route: getRoute(EDashboardCounterType.InProgress),
        color: 'yellow',
        className: styles['header-counter'],
      },
      {
        count: counters.overdue,
        label: formatMessage({ id: 'dashboard.overdue' }) as string,
        route: getRoute(EDashboardCounterType.Overdue),
        color: 'red',
        className: styles['header-counter'],
      },
      {
        count: counters.completed,
        label: formatMessage({ id: 'dashboard.counter-completed' }) as string,
        route: getRoute(EDashboardCounterType.Completed),
        color: 'green',
        className: styles['header-counter'],
      },
    ];
  };

  const activitesTooltipText =
    props.dashboardMode === EDashboardModes.Tasks
      ? 'dashboard.tasks-breakdown.tooltip-text'
      : 'dashboard.workflow-breakdown.tooltip-text';

  return (
    <div className={classnames(styles['container'])}>
      <div className={styles['info']}>
        <div className={styles['cards__wrapper']}>
          <DashboardCounters
            isLoading={props.isLoading}
            counterLoader={<Loader containerClassName={styles['counter-loader']} isLoading isCentered={false} />}
            countersParamsList={countersParamsList()}
          />
        </div>
        <div className={styles['activities']}>
          <IntlMessages id={activitiesTitle}>
            {(text) => (
              <div className={styles['activities__header']}>
                <Header tag="h3" size="4" className={styles['checkout-header']}>
                  {text}
                </Header>
                <span
                  ref={tooltipIconRef}
                  className={styles['tooltip-container']}
                  aria-expanded={isTooltipShown}
                  aria-labelledby="dashboard-workflow-breakdown-tooltip"
                  onMouseOver={() => setIsTooltipShown(true)}
                  onMouseLeave={() => setIsTooltipShown(false)}
                >
                  <FilledInfoIcon className={styles['tooltip-icon']} fill="#DCDCDB" />
                  <CustomTooltip
                    id="dashboard-workflow-breakdown-tooltip"
                    isOpen={isTooltipShown}
                    target={tooltipIconRef}
                    tooltipText={activitesTooltipText}
                    placement={ETooltipPlacement.Top}
                    tooltipClassName={styles['dashboard__tooltip']}
                  />
                </span>
              </div>
            )}
          </IntlMessages>

          <Breakdowns
            breakdownItems={props.breakdownItems}
            mode={props.dashboardMode}
            isLoading={props.isLoading}
            openSelectTemplateModal={props.openSelectTemplateModal}
            loadBreakdownTasks={props.loadBreakdownTasks}
            settingsChanged={props.settingsChanged}
            openRunWorkflowModalOnDashboard={props.openRunWorkflowModalOnDashboard}
          />
        </div>
        <div className={styles['widgets']}>
          <DashboardWidgets />
        </div>
      </div>
    </div>
  );
};
