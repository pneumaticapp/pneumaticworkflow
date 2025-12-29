import React, { ReactNode, useEffect, useMemo } from 'react';
import { matchPath } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { TasksSortingContainer } from './TasksSortingContainer';
import { TLoadTasksFilterStepsPayload } from '../../redux/actions';
import { loadWorkflowsList } from '../../redux/workflows/slice';
import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { FilterIcon } from '../../components/icons';
import { FilterSelect, Tabs, ReturnLink } from '../../components/UI';
import { checkSomeRouteIsActive, history } from '../../utils/history';
import { reactElementToText } from '../../utils/reactElementToText';
import { ITopNavOwnProps } from '../../components/TopNav/TopNav';
import {
  ETaskListCompleteSorting,
  ETaskListCompletionStatus,
  ETaskListSorting,
  ITemplateStep,
} from '../../types/tasks';
import { ITemplateTitleBaseWithCount } from '../../types/template';
import { StepName } from '../../components/StepName';
import { WorkflowModalContainer } from '../../components/Workflows/WorkflowModal';

import styles from './TasksLayout.css';

export interface ITasksLayoutStoreProps {
  children?: ReactNode;
  isHasFilter: boolean;
  sorting: ETaskListSorting | ETaskListCompleteSorting;
  filterTemplates: ITemplateTitleBaseWithCount[];
  filterSteps: ITemplateStep[];
  templateIdFilter: number | null;
  taskApiNameFilter: string | null;
  completionStatus: ETaskListCompletionStatus;
}

export interface ITasksLayoutDispatchProps {
  loadTasksFilterTemplates(): void;
  loadTasksFilterSteps(payload: TLoadTasksFilterStepsPayload): void;
  setTasksFilterTemplate(value: number | null): void;
  setTasksFilterStep(apiName: string | null): void;
  closeWorkflowLogPopup(): void;
  changeTasksCompleteStatus(status: ETaskListCompletionStatus): void;
  clearFilters(): void;
  changeTasksSorting(status: ETaskListSorting | ETaskListCompleteSorting): void;
}

type TTasksLayoutProps = ITasksLayoutStoreProps & ITasksLayoutDispatchProps;

export function TasksLayoutComponent({
  children,
  isHasFilter,
  sorting,
  filterTemplates,
  filterSteps,
  templateIdFilter,
  taskApiNameFilter,
  completionStatus,
  loadTasksFilterTemplates,
  loadTasksFilterSteps,
  setTasksFilterTemplate,
  setTasksFilterStep,
  closeWorkflowLogPopup,
  changeTasksCompleteStatus,
  clearFilters,
  changeTasksSorting,
}: TTasksLayoutProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const optionsWithoutCount = useMemo(() => {
    return filterTemplates.map(({ id, name }) => ({
      id,
      name,
    }));
  }, [filterTemplates]);

  useEffect(() => {
    loadTasksFilterTemplates();
  }, []);

  useEffect(() => {
    if (templateIdFilter != null) {
      loadTasksFilterSteps({ templateId: templateIdFilter });
    }
  }, [templateIdFilter]);

  const renderTaskDetailLeftContent = () => {
    return <ReturnLink label={formatMessage({ id: 'menu.tasks' })} route={ERoutes.Tasks} />;
  };

  const getStepsFilterOptions = () => {
    if (!templateIdFilter) {
      return [];
    }

    const options = filterSteps.map(({ name, id, apiName }) => {
      const stepName =
        typeof name === 'string' ? <StepName initialStepName={name} templateId={templateIdFilter} /> : name;

      return {
        id,
        name: stepName,
        searchByText: reactElementToText(stepName),
        apiName,
        customClickHandler: () => {
          setTasksFilterStep(apiName);
        },
      };
    });

    return options;
  };

  const renderTaskListContent = () => {
    function mapSorting(
      taskStatus: ETaskListCompletionStatus,
      value: ETaskListSorting | ETaskListCompleteSorting,
    ): ETaskListSorting | ETaskListCompleteSorting {
      if (taskStatus === ETaskListCompletionStatus.Completed) {
        switch (value) {
          case ETaskListCompleteSorting.DateAsc:
            return ETaskListCompleteSorting.DateAsc;
          case ETaskListCompleteSorting.DateDesc:
            return ETaskListCompleteSorting.DateDesc;
          default:
            return ETaskListCompleteSorting.DateDesc;
        }
      }

      switch (value) {
        case ETaskListSorting.DateAsc:
          return ETaskListSorting.DateAsc;
        case ETaskListSorting.DateDesc:
          return ETaskListSorting.DateDesc;
        case ETaskListSorting.Overdue:
          return ETaskListSorting.Overdue;
        default:
          return ETaskListSorting.DateDesc;
      }
    }

    return (
      <div className={styles['navbar-left__content']}>
        <div className={styles['filters']}>
          <Tabs
            activeValueId={completionStatus}
            values={[
              {
                id: ETaskListCompletionStatus.Active,
                label: formatMessage({ id: 'menu.workflows.in-progress' }),
              },
              {
                id: ETaskListCompletionStatus.Completed,
                label: formatMessage({ id: 'menu.workflows.completed' }),
              },
            ]}
            onChange={(value) => {
              changeTasksCompleteStatus(value);
              loadTasksFilterTemplates();

              if (templateIdFilter) {
                loadTasksFilterSteps({ templateId: templateIdFilter });
              }

              changeTasksSorting(mapSorting(value, sorting));
            }}
            containerClassName={styles['completion-status-tabs']}
          />
          <div className={styles['template-filter']}>
            <FilterSelect
              isSearchShown
              noValueLabel={formatMessage({ id: 'sorting.all-templates' })}
              placeholderText={formatMessage({ id: 'sorting.no-template-found' })}
              selectedOption={templateIdFilter}
              options={optionsWithoutCount}
              optionIdKey="id"
              optionLabelKey="name"
              onChange={setTasksFilterTemplate}
              resetFilter={() => setTasksFilterTemplate(null)}
              Icon={FilterIcon}
              renderPlaceholder={(templates) => {
                const activeOption = templates.find((t) => t.id === templateIdFilter);

                return activeOption?.name || formatMessage({ id: 'sorting.all-templates' });
              }}
            />
          </div>
          {templateIdFilter && (
            <div className={styles['step-filter']}>
              <FilterSelect
                isSearchShown
                noValueLabel={formatMessage({ id: 'sorting.all-steps' })}
                placeholderText={formatMessage({ id: 'sorting.no-step-found' })}
                selectedOption={taskApiNameFilter}
                options={getStepsFilterOptions()}
                optionIdKey="id"
                optionLabelKey="name"
                onChange={() => {}}
                resetFilter={() => setTasksFilterStep(null)}
                Icon={FilterIcon}
                renderPlaceholder={(steps) => {
                  const activeOption = steps.find((s) => s.apiName === taskApiNameFilter);

                  return activeOption?.name || formatMessage({ id: 'sorting.all-steps' });
                }}
              />
            </div>
          )}
          <TasksSortingContainer />
          {isHasFilter && (
            <button type="button" onClick={clearFilters} className="cancel-button">
              {formatMessage({ id: 'tasks.clear-filters' })}
            </button>
          )}
        </div>
      </div>
    );
  };

  const topNavProps = () => {
    const propsMap: { [key: string]: ITopNavOwnProps } = {
      [ERoutes.TaskDetail]: {
        leftContent: renderTaskDetailLeftContent(),
      },
      [ERoutes.Tasks]: {
        leftContent: renderTaskListContent(),
      },
    };

    const { pathname } = history.location;
    const currentRoute = Object.keys(propsMap).find((route) => matchPath(pathname, route));

    return currentRoute ? propsMap[currentRoute] : {};
  };

  return (
    <>
      <TopNavContainer {...topNavProps()} />
      <main>
        <div className="container-fluid">{children}</div>
      </main>
      <WorkflowModalContainer
        onWorkflowEnded={() => {
          dispatch(loadWorkflowsList(0));
          closeWorkflowLogPopup();
        }}
        onWorkflowSnoozed={() => {
          closeWorkflowLogPopup();

          if (checkSomeRouteIsActive(ERoutes.TaskDetail)) {
            history.push(ERoutes.Tasks);
          }
        }}
      />
    </>
  );
}
