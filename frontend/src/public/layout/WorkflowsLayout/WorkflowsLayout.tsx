/* eslint-disable consistent-return */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { loadWorkflowsList, TRemoveWorkflowFromListPayload } from '../../redux/actions';
import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { WorkflowModalContainer } from '../../components/Workflows/WorkflowModal';
import { SelectMenu, Tabs } from '../../components/UI';
import { EWorkflowsSorting, EWorkflowsStatus, EWorkflowsView, ITemplateFilterItem } from '../../types/workflow';
import { BoxesIcon, StatusTitlesIcon, TableViewIcon } from '../../components/icons';
import { IWorkflowsFiltersProps } from '../../components/Workflows/types';
import {
  canFilterByCurrentPerformer,
  canFilterByTemplateStep,
  checkSortingIsIncorrect,
  getSortingsByStatus,
} from '../../utils/workflows/filters';

import {
  TableViewContainerRef,
  WorkflowsTableActions,
} from '../../components/Workflows/WorkflowsTablePage/WorkflowsTable';
import { WorkflowsTableProvider } from '../../components/Workflows/WorkflowsTablePage/WorkflowsTable/WorkflowsTableContext';

import { IApplicationState } from '../../types/redux';
import { useCheckDevice } from '../../hooks/useCheckDevice';
import { StarterFilterSelect } from './StarterFilterSelect';
import { TemplateFilterSelect } from './TemplateFilterSelect';
import { PerformerFilterSelect } from './PerformerFilterSelect';
import { TaskFilterSelect } from './TaskFilterSelect';

import styles from './WorkflowsLayout.css';

export interface IWorkflowsLayoutComponentProps extends IWorkflowsFiltersProps {
  workflowId: number | null;
  workflowsView: EWorkflowsView;
  children: React.ReactNode;
  closeWorkflowLogPopup(): void;
  removeWorkflowFromList(payload: TRemoveWorkflowFromListPayload): void;
  setWorkflowsView(view: EWorkflowsView): void;
}

export function WorkflowsLayoutComponent({
  children,
  workflowId,
  filterTemplates,
  templatesIdsFilter,
  statusFilter,
  sorting,
  stepsIdsFilter,
  performersIdsFilter,
  workflowStartersIdsFilter,
  workflowsView,
  areFiltersChanged,
  clearFilters,
  setWorkflowsView,
  changeWorkflowsSorting,
  setStatusFilter,
  applyFilters,
  loadTemplatesTitles,
  setStepsFilter,
  removeWorkflowFromList,
  loadTemplateSteps,
  updateCurrentPerformersCounters,
  updateWorkflowsTemplateStepsCounters,
  updateWorkflowStartersCounters,
}: IWorkflowsLayoutComponentProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const { isMobile } = useCheckDevice();
  const workflowsLoadingStatus = useSelector((state: IApplicationState) => state.workflows.workflowsLoadingStatus);
  const [isTableWiderThanScreen, setIsTableWiderThanScreen] = useState(false);
  const workflowsMainRef = useRef<HTMLDivElement>(null);
  const tableViewContainerRef = useRef<TableViewContainerRef>(null);

  const selectedTemplates: ITemplateFilterItem[] = useMemo(() => {
    const filterTemplatesMap: Map<number, ITemplateFilterItem> = new Map(
      filterTemplates.map((template) => [template.id, template]),
    );

    return templatesIdsFilter
      .map((templateId) => filterTemplatesMap.get(templateId))
      .filter(Boolean) as ITemplateFilterItem[];
  }, [templatesIdsFilter, filterTemplates]);

  const prevTemplatesIdsFilterRef = React.useRef<number[]>([]);

  useEffect(() => {
    if (workflowsView !== EWorkflowsView.Table) {
      return;
    }

    const checkWidth = () => {
      if (workflowsMainRef.current && tableViewContainerRef.current?.element) {
        const isWider = tableViewContainerRef.current.element.scrollWidth > workflowsMainRef.current.clientWidth;
        setIsTableWiderThanScreen(isWider);
      }
    };

    const setupObserver = () => {
      if (!tableViewContainerRef.current?.element) {
        setTimeout(setupObserver, 100);
        return;
      }

      const observer = new ResizeObserver(checkWidth);
      observer.observe(tableViewContainerRef.current.element);

      window.addEventListener('resize', checkWidth);
      checkWidth();

      return () => {
        window.removeEventListener('resize', checkWidth);
        observer.disconnect();
      };
    };

    return setupObserver();
  }, [workflowsView]);

  useEffect(() => {
    if (templatesIdsFilter.length === 0) {
      setStepsFilter([]);
      prevTemplatesIdsFilterRef.current = [];
      return;
    }

    const prevTemplatesIdsSet = new Set(prevTemplatesIdsFilterRef.current);

    const currentTemplateTaskIdsSet = new Set(
      selectedTemplates.flatMap((template) => template.steps.map((step) => step.id)),
    );
    const prevTemplatesActualTaskIds = stepsIdsFilter.filter((id) => currentTemplateTaskIdsSet.has(id));

    const addedTemplates = selectedTemplates.filter((template) => !prevTemplatesIdsSet.has(template.id));
    addedTemplates.forEach((template) => {
      const hasTasks = template.steps.length > 0;
      if (!hasTasks && !template.areStepsLoading) {
        loadTemplateSteps({ templateId: template.id });
      }
    });

    const allNewTemplatesTasksLoaded = addedTemplates.every((template) => template.steps.length > 0);
    if (allNewTemplatesTasksLoaded) {
      const allStepIds = [
        ...prevTemplatesActualTaskIds,
        ...addedTemplates.flatMap((template) => template.steps.map((steps) => steps.id)),
      ];
      setStepsFilter(allStepIds);
      if (canFilterByTemplateStep(statusFilter)) {
        updateWorkflowsTemplateStepsCounters();
      }
    }

    prevTemplatesIdsFilterRef.current = templatesIdsFilter;
  }, [templatesIdsFilter, selectedTemplates, statusFilter]);

  useEffect(() => {
    loadTemplatesTitles();
  }, [statusFilter]);

  useEffect(() => {
    if (canFilterByCurrentPerformer(statusFilter)) {
      updateCurrentPerformersCounters();
    }
  }, [statusFilter, templatesIdsFilter, stepsIdsFilter, workflowStartersIdsFilter]);

  useEffect(() => {
    if (canFilterByTemplateStep(statusFilter)) {
      updateWorkflowsTemplateStepsCounters();
    }
  }, [statusFilter, templatesIdsFilter, performersIdsFilter, workflowStartersIdsFilter]);

  useEffect(() => {
    updateWorkflowStartersCounters();
  }, [statusFilter, templatesIdsFilter, performersIdsFilter]);

  useEffect(() => {
    applyFilters();
  }, [statusFilter, templatesIdsFilter, stepsIdsFilter, performersIdsFilter, workflowStartersIdsFilter, sorting]);

  useEffect(() => {
    if (checkSortingIsIncorrect(statusFilter, sorting)) {
      changeWorkflowsSorting(EWorkflowsSorting.DateDesc);
    }
  }, [sorting, statusFilter]);

  const statusTitles = React.useMemo(() => Object.values(EWorkflowsStatus), []);
  const sortingTitles = React.useMemo(() => getSortingsByStatus(statusFilter), [statusFilter]);

  const renderLeftContent = () => {
    return (
      <div className={styles['navbar-left-content']}>
        <div className={styles['filters']}>
          <Tabs
            activeValueId={workflowsView}
            tabClassName={styles['view-switch-tab']}
            values={[
              {
                id: EWorkflowsView.Table,
                label: <TableViewIcon />,
              },
              {
                id: EWorkflowsView.Grid,
                label: <BoxesIcon />,
              },
            ]}
            onChange={(view) => {
              if (view === EWorkflowsView.Table) {
                sessionStorage.setItem('isInternalNavigation', 'true');
              }
              setWorkflowsView(view);
            }}
          />

          {renderFilters()}
        </div>
      </div>
    );
  };

  const renderFilters = () => {
    return (
      <>
        <TemplateFilterSelect />
        <StarterFilterSelect />
        <SelectMenu
          values={statusTitles}
          activeValue={statusFilter}
          onChange={setStatusFilter}
          Icon={StatusTitlesIcon}
          withRadio
        />
        <TaskFilterSelect selectedTemplates={selectedTemplates} />
        <PerformerFilterSelect />
        <SelectMenu values={sortingTitles} activeValue={sorting} onChange={changeWorkflowsSorting} withRadio />
        {areFiltersChanged && (
          <button type="button" onClick={clearFilters} className="cancel-button">
            {formatMessage({ id: 'workflows.clear-table-filters' })}
          </button>
        )}
      </>
    );
  };

  const handleCloseWorkflowLogPopup = () => {
    const newUrl = ERoutes.Workflows + history.location.search;
    history.push(newUrl);
  };

  return (
    <main
      ref={workflowsMainRef}
      id="workflows-main"
      className={workflowsView === EWorkflowsView.Table ? styles['workflows-main'] : ''}
    >
      <TopNavContainer leftContent={renderLeftContent()} isFromWorkflowsLayout workflowsView={workflowsView} />
      <WorkflowsTableProvider value={{ ref: tableViewContainerRef, isTableWiderThanScreen }}>
        {workflowsView === EWorkflowsView.Table && (isTableWiderThanScreen || isMobile) && (
          <WorkflowsTableActions workflowsLoadingStatus={workflowsLoadingStatus} isWideTable isMobile={isMobile} />
        )}
        <div className="container-fluid">{children}</div>

        <WorkflowModalContainer
          onClose={handleCloseWorkflowLogPopup}
          onWorkflowEnded={() => {
            dispatch(loadWorkflowsList(0));
          }}
          onWorkflowDeleted={() => removeWorkflowFromList({ workflowId })}
        />
      </WorkflowsTableProvider>
    </main>
  );
}
