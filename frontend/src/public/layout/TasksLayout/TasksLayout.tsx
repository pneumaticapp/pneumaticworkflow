import React, { ReactNode, useEffect, useMemo } from 'react';
import { matchPath } from 'react-router-dom';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { TasksSorting } from './TasksSorting';
import { loadWorkflowsList } from '../../redux/workflows/slice';
import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { FilterIcon } from '../../components/icons';
import { Tabs, ReturnLink } from '../../components/UI';
import { Select } from '../../components/UI/Select';
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
import { TLoadFilterStepsPayload } from '../../redux/tasks/types';

export interface ITasksLayoutStoreProps {
  children?: ReactNode;
  isHasFilter: boolean;
  sorting: ETaskListSorting | ETaskListCompleteSorting;
  filterTemplates: ITemplateTitleBaseWithCount[];
  filterSteps: ITemplateStep[];
  areFilterTemplatesLoading: boolean;
  areFilterStepsLoading: boolean;
  templateIdFilter: number | null;
  taskApiNameFilter: string | null;
  completionStatus: ETaskListCompletionStatus;
}

export interface ITasksLayoutDispatchProps {
  loadFilterTemplates(): void;
  loadFilterSteps(payload: TLoadFilterStepsPayload): void;
  setFilterTemplate(value: number | null): void;
  setFilterStep(apiName: string | null): void;
  closeWorkflowLogPopup(): void;
  changeTaskListCompletionStatus(status: ETaskListCompletionStatus): void;
  clearFilters(): void;
  changeTaskListSorting(status: ETaskListSorting | ETaskListCompleteSorting): void;
}

type TTasksLayoutProps = ITasksLayoutStoreProps & ITasksLayoutDispatchProps;

export function TasksLayoutComponent({
  children,
  isHasFilter,
  sorting,
  filterTemplates,
  filterSteps,
  areFilterTemplatesLoading,
  areFilterStepsLoading,
  templateIdFilter,
  taskApiNameFilter,
  completionStatus,
  loadFilterTemplates,
  loadFilterSteps,
  setFilterTemplate,
  setFilterStep,
  closeWorkflowLogPopup,
  changeTaskListCompletionStatus,
  clearFilters,
  changeTaskListSorting,
}: TTasksLayoutProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const templateOptions = useMemo(() => {
    const options = filterTemplates.map(({ id, name }) => ({ value: String(id), label: name }));

    return templateIdFilter === null
      ? options
      : [{ value: '', label: formatMessage({ id: 'sorting.all-templates' }) }, ...options];
  }, [filterTemplates, templateIdFilter, formatMessage]);

  useEffect(() => {
    loadFilterTemplates();
  }, []);

  useEffect(() => {
    if (templateIdFilter != null) {
      loadFilterSteps({ templateId: templateIdFilter });
    }
  }, [templateIdFilter]);

  const renderTaskDetailLeftContent = () => {
    return <ReturnLink label={formatMessage({ id: 'menu.tasks' })} route={ERoutes.Tasks} />;
  };

  const getStepsFilterOptions = () => {
    if (!templateIdFilter) {
      return [];
    }

    const options = filterSteps.map(({ name, apiName }) => {
      const stepName =
        typeof name === 'string' ? <StepName initialStepName={name} templateId={templateIdFilter} /> : name;

      return { value: apiName, label: stepName, searchByText: reactElementToText(stepName) };
    });

    return taskApiNameFilter === null
      ? options
      : [{ value: '', label: formatMessage({ id: 'sorting.all-steps' }) }, ...options];
  };

  const renderTaskListContent = () => {
    const stepOptions = getStepsFilterOptions();

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
              changeTaskListCompletionStatus(value);
              loadFilterTemplates();

              if (templateIdFilter) {
                loadFilterSteps({ templateId: templateIdFilter });
              }

              changeTaskListSorting(mapSorting(value, sorting));
            }}
            containerClassName={styles['completion-status-tabs']}
          />
          <div className={styles['template-filter']}>
            <Select
              controlSize="sm"
              controlVariant="accent"
              Icon={FilterIcon}
              isSearchable
              isLoading={areFilterTemplatesLoading}
              title={templateIdFilter === null ? formatMessage({ id: 'sorting.all-templates' }) : ''}
              noOptionsMessage={() => formatMessage({ id: 'sorting.no-template-found' })}
              options={templateOptions}
              value={templateOptions.find((option) => option.value === String(templateIdFilter)) ?? null}
              onChange={({ value }: { value: string }) => setFilterTemplate(value ? Number(value) : null)}
              classNames={{ menuList: () => styles['template-filter__menu'] }}
            />
          </div>
          {templateIdFilter && (
            <div className={styles['step-filter']}>
              <Select
                controlSize="sm"
                controlVariant="accent"
                Icon={FilterIcon}
                isSearchable
                isLoading={areFilterStepsLoading}
                title={taskApiNameFilter === null ? formatMessage({ id: 'sorting.all-steps' }) : ''}
                noOptionsMessage={() => formatMessage({ id: 'sorting.no-step-found' })}
                options={stepOptions}
                value={stepOptions.find((option) => option.value === taskApiNameFilter) ?? null}
                onChange={({ value }: { value: string }) => setFilterStep(value || null)}
              />
            </div>
          )}
          <TasksSorting />
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
