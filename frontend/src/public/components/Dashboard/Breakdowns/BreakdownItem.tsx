/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count
import * as React from 'react';
import { history } from '../../../utils/history';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { Link } from 'react-router-dom';

import { EIntegrations } from '../../../types/integrations';
import { TemplateIntegrationsIndicator } from '../../TemplateIntegrationsStats';
import { IDashboardCounterProps } from '../Counters';
import { EDashboardModes, TDashboardBreakdownItem } from '../../../types/redux';
import { DashboardCounters } from '../Counters/DashboardCounters';
import { ILoadBreakdownTasksPayload } from '../../../redux/dashboard/actions';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { getLinkToTemplate } from '../../../utils/routes/getLinkToTemplate';
import { EDashboardCounterType } from '../Counters/types';
import { getLinkToTasks } from '../../../utils/routes/getLinkToTasks';
import { ETaskListCompletionStatus, ETaskListSorting } from '../../../types/tasks';
import { EWorkflowsSorting, EWorkflowsStatus } from '../../../types/workflow';
import { Button } from '../../UI/Buttons/Button';
import { getTotalTasksCount } from '../../../utils/dashboard';
import {
  EditIcon,
  RunWorkflowIcon,
  ConnectedIcon,
  DisconnectedIcon,
  MoreIcon,
  IntegrateIcon,
  PencilIcon,
  PlayLogoIcon,
  WorkflowOpen,
  WorkflowMinimize,
} from '../../icons';
import { Dropdown, Header, Loader, TDropdownOption } from '../../UI';
import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { IntegrateButton } from '../../IntegrateButton';

import { TaskItem } from './TaskItem';

import styles from './Breakdowns.css';
import { ShortArrowBox } from '../../UI/ShortArrowBox';

export interface IBreakdownItemProps {
  breakdown: TDashboardBreakdownItem;
  mode: EDashboardModes;
  loadBreakdownTasks(payload: ILoadBreakdownTasksPayload): void;
  openRunWorkflowModalOnDashboard({ templateId }: { templateId: number }): void;
}

const { useState, useCallback } = React;

export function BreakdownItem({
  breakdown,
  mode,
  loadBreakdownTasks,
  openRunWorkflowModalOnDashboard,
}: IBreakdownItemProps) {
  const { isDesktop, isMobile } = useCheckDevice();
  const [showBreakdownTasks, setShowBreakdownTasks] = useState(false);
  const [areIntegrationsVisible, setIntegrationsVisible] = useState(false);

  const { formatMessage } = useIntl();

  const getRoute = useCallback(
    (counterType: EDashboardCounterType) => {
      const { templateId } = breakdown;

      const tasksRouteMap = {
        [EDashboardCounterType.Started]: getLinkToTasks({ templateId }),
        [EDashboardCounterType.InProgress]: getLinkToTasks({ templateId }),
        [EDashboardCounterType.Overdue]: getLinkToTasks({ templateId, sorting: ETaskListSorting.Overdue }),
        [EDashboardCounterType.Completed]: getLinkToTasks({ templateId, status: ETaskListCompletionStatus.Completed }),
      };

      const workflowsRouteMap = {
        [EDashboardCounterType.Started]: getLinkToWorkflows({
          templateId,
        }),
        [EDashboardCounterType.InProgress]: getLinkToWorkflows({
          templateId,
        }),
        [EDashboardCounterType.Overdue]: getLinkToWorkflows({
          templateId,
          sorting: EWorkflowsSorting.Overdue,
        }),
        [EDashboardCounterType.Completed]: getLinkToWorkflows({
          templateId,
          status: EWorkflowsStatus.Completed,
        }),
      };

      const routeMap = {
        [EDashboardModes.Workflows]: workflowsRouteMap,
        [EDashboardModes.Tasks]: tasksRouteMap,
      };

      return routeMap[mode][counterType];
    },
    [mode],
  );

  const countersParamsList: () => IDashboardCounterProps[] = () => [
    {
      count: breakdown.started,
      color: 'blue',
      className: classnames(styles.breakdown__card, styles['breakdown__card-blue']),
      route: getRoute(EDashboardCounterType.Started),
      tooltipLabel: formatMessage({ id: 'dashboard.counter-launched' }),
    },
    {
      count: breakdown.inProgress,
      color: 'yellow',
      className: classnames(styles.breakdown__card, styles['breakdown__card-yellow']),
      route: getRoute(EDashboardCounterType.InProgress),
      tooltipLabel: formatMessage({ id: 'dashboard.counter-ongoing' }),
    },
    {
      count: breakdown.overdue,
      color: 'red',
      className: classnames(styles.breakdown__card, styles['breakdown__card-red']),
      route: getRoute(EDashboardCounterType.Overdue),
      tooltipLabel: formatMessage({ id: 'dashboard.overdue' }),
    },
    {
      count: breakdown.completed,
      color: 'green',
      className: classnames(
        styles.breakdown__card,
        styles['breakdown__card-green'],
        mode === EDashboardModes.Tasks && styles['breakdown__card-no_link'],
      ),
      route: getRoute(EDashboardCounterType.Completed),
      tooltipLabel: formatMessage({ id: 'dashboard.counter-completed' }),
    },
  ];

  React.useEffect(() => {
    if (showBreakdownTasks) {
      loadBreakdownTasks({ templateId: breakdown.templateId });
    }
  }, [showBreakdownTasks]);

  const handleToggleBreakdownTasks = () => {
    setShowBreakdownTasks(!showBreakdownTasks);
  };

  const renderTasks = () => {
    if (!showBreakdownTasks) {
      return null;
    }

    if (breakdown.areTasksLoading) {
      return (
        <div
          className={classnames(
            styles.breakdown__tasks,
            mode === EDashboardModes.Tasks
              ? styles['breakdown__tasks-mode-tasks']
              : styles['breakdown__tasks-mode-worflows'],
          )}
        >
          <Loader isLoading isCentered={false} containerClassName={styles['breadown__loader']} />
        </div>
      );
    }

    return (
      <div
        className={classnames(
          styles.breakdown__tasks,
          mode === EDashboardModes.Tasks
            ? styles['breakdown__tasks-mode-tasks']
            : styles['breakdown__tasks-mode-worflows'],
        )}
      >
        {breakdown.tasks.map((task, index) => {
          if (mode === EDashboardModes.Tasks && getTotalTasksCount(task) === 0) {
            return null;
          }

          return <TaskItem key={task.id} task={task} index={index} mode={mode} templateId={breakdown.templateId} />;
        })}
      </div>
    );
  };

  const onRunWorkflows = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    openRunWorkflowModalOnDashboard({ templateId: breakdown.templateId });
  };

  const renderCounters = () => {
    return (
      <div className={classnames(styles['breakdown__counters'])}>
        <DashboardCounters
          countersParamsList={countersParamsList()}
          className={styles['breakdown__dashboard_cards']}
          labelClassName={styles['breakdown__dashboard_cards_label']}
        />
      </div>
    );
  };

  const renderControls = () => {
    const editButton = (
      <Button
        size="sm"
        buttonStyle="transparent-black"
        label={formatMessage({ id: 'dashboard.edit' })}
        wrapper={Link}
        to={getLinkToTemplate({ templateId: breakdown.templateId })}
        icon={EditIcon}
      />
    );

    const runWorkflowButton = (
      <Button
        type="button"
        size="sm"
        buttonStyle="yellow"
        label={formatMessage({ id: 'dashboard.run-workflow' })}
        onClick={onRunWorkflows}
        icon={RunWorkflowIcon}
      />
    );

    const buttonsMap = [
      {
        check: () => breakdown.isActive,
        render: () => (
          <div className={styles['controls']}>
            {runWorkflowButton}
            {editButton}
            <IntegrateButton
              tepmlateId={breakdown.templateId}
              isVisible={areIntegrationsVisible}
              toggle={() => setIntegrationsVisible(!areIntegrationsVisible)}
              linksType="relative"
              isFromBreakdownItem
            />
          </div>
        ),
      },
      {
        check: () => !breakdown.isActive,
        render: () => editButton,
      },
    ];

    return (
      <div className={classnames(styles['action-buttons-container'])}>
        {buttonsMap.find(({ check }) => check())?.render()}
      </div>
    );
  };

  const isPossibleToToggle = getTotalTasksCount(breakdown) !== 0;

  const toggleBreakdownHandler = useCallback(() => {
    return isPossibleToToggle ? handleToggleBreakdownTasks() : () => null;
  }, [isPossibleToToggle, handleToggleBreakdownTasks]);

  const handleOptionClick = (handler: Function) => (closeDropdown: () => void) => {
    closeDropdown();
    if (handler.length > 0) {
      handler({ preventDefault: () => {}, stopPropagation: () => {} });
    } else {
      handler();
    }
  };

  const WorkflowsOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'templates.run-workflow' }),
      onClick: handleOptionClick(onRunWorkflows),
      Icon: PlayLogoIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'workflows.edit-template' }),
      onClick: handleOptionClick(() => history.push(getLinkToTemplate({ templateId: breakdown.templateId }) as string)),
      Icon: PencilIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'template.more-integrate-template' }),
      onClick: handleOptionClick(() => setIntegrationsVisible(!areIntegrationsVisible)),
      Icon: IntegrateIcon,
      size: 'sm',
    },
  ];
  const openButton: TDropdownOption = {
    label: formatMessage({ id: 'workflows.open' }),
    onClick: toggleBreakdownHandler,
    Icon: WorkflowOpen,
    size: 'sm',
  };
  const minimizeButton: TDropdownOption = {
    label: formatMessage({ id: 'workflows.minimize' }),
    onClick: toggleBreakdownHandler,
    Icon: WorkflowMinimize,
    size: 'sm',
  };
  const MobileMyTasksOptions = [showBreakdownTasks ? minimizeButton : openButton];

  const renderBreakdownMap = {
    [EDashboardModes.Workflows]: () => {
      return (
        <div className={classnames(styles.breakdown, !breakdown.isActive && styles['breakdown_draft'])}>
          <div className={classnames(styles['breakdown__container-wrapper'])}>
            {isDesktop && (
              <ShortArrowBox rotated={showBreakdownTasks} toggleBreakdownHandler={toggleBreakdownHandler} />
            )}
            <div
              className={classnames(
                styles.breakdown__container,
                isPossibleToToggle ? null : styles.breakdown__container_no_toggle,
              )}
            >
              <div className={styles['breakdown__head_container-wrapper']}>
                <div className={styles.breakdown__head_container}>
                  <div className={styles.breakdown__title}>
                    {isDesktop && (
                      <TemplateIntegrationsIndicator
                        templateId={breakdown.templateId}
                        exlcude={[EIntegrations.Webhooks]}
                        integratedIndicator={
                          <div className={styles['indicator-icon']}>
                            <ConnectedIcon />
                          </div>
                        }
                        disconnectedIndicator={
                          <div className={styles['indicator-icon']}>
                            <DisconnectedIcon />
                          </div>
                        }
                      />
                    )}

                    <Header
                      className={classnames(
                        styles['breakdown__title-text'],
                        styles['breakdown__title-text_with-image'],
                      )}
                      size="6"
                      tag="p"
                    >
                      {isDesktop ? (
                        <Link
                          to={getLinkToWorkflows({
                            templateId: breakdown.templateId,
                          })}
                          className={styles['breakdown__title-link']}
                          onClick={() => {
                            sessionStorage.setItem('shouldLoadPresets', 'true');
                          }}
                        >
                          {breakdown.templateName}
                        </Link>
                      ) : (
                        <button
                          type="button"
                          onClick={toggleBreakdownHandler}
                          className={styles['breakdown__title-button']}
                        >
                          {breakdown.templateName}
                        </button>
                      )}
                    </Header>
                  </div>
                </div>
                {isMobile && (
                  <Dropdown
                    isFromBreakdownItem
                    renderToggle={() => <MoreIcon className={styles['card__more']} />}
                    options={[...MobileMyTasksOptions, ...WorkflowsOptions]}
                  />
                )}
              </div>

              {renderCounters()}
            </div>
            {isDesktop && (
              <Dropdown
                isFromBreakdownItem
                renderToggle={() => <MoreIcon className={styles['card__more']} />}
                options={WorkflowsOptions}
              />
            )}
          </div>
          {renderTasks()}
          {showBreakdownTasks && renderControls()}
        </div>
      );
    },
    [EDashboardModes.Tasks]: () => {
      return (
        <div className={styles.breakdown}>
          <div className={classnames(styles['breakdown__container-wrapper'])}>
            {isDesktop && (
              <ShortArrowBox rotated={showBreakdownTasks} toggleBreakdownHandler={toggleBreakdownHandler} />
            )}
            <div
              className={classnames(
                styles.breakdown__container,
                isPossibleToToggle ? null : styles.breakdown__container_no_toggle,
              )}
            >
              <div className={styles['breakdown__head_container-wrapper']}>
                <div className={styles.breakdown__head_container}>
                  <div className={styles.breakdown__title}>
                    <Header className={classnames(styles['breakdown__title-text'])} size="6" tag="p">
                      {isDesktop ? (
                        <Link
                          to={getLinkToTasks({ templateId: breakdown.templateId })}
                          className={styles['breakdown__title-link']}
                        >
                          {breakdown.templateName}
                        </Link>
                      ) : (
                        <button
                          type="button"
                          onClick={toggleBreakdownHandler}
                          className={styles['breakdown__title-button']}
                        >
                          {breakdown.templateName}
                        </button>
                      )}
                    </Header>
                  </div>
                </div>
                {isMobile && (
                  <Dropdown
                    isFromBreakdownItem
                    renderToggle={() => <MoreIcon className={styles['card__more']} />}
                    options={MobileMyTasksOptions}
                  />
                )}
              </div>
              {renderCounters()}
            </div>
            {isDesktop && (
              <Dropdown
                isFromBreakdownItem
                renderToggle={() => (
                  <MoreIcon className={classnames(styles['card__more_disabled'], styles['card__more'])} />
                )}
                options={[]}
                isDisabled={true}
              />
            )}
          </div>
          {renderTasks()}
        </div>
      );
    },
  };

  return renderBreakdownMap[mode]();
}
