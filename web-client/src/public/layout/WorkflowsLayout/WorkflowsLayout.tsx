import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';

import { TRemoveWorkflowFromListPayload } from '../../redux/actions';
import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { WorkflowModalContainer } from '../../components/Workflows/WorkflowModal';
import { FilterSelect, SelectMenu, Tabs } from '../../components/UI';
import { EWorkflowsSorting, EWorkflowsStatus, EWorkflowsView } from '../../types/workflow';
import { FilterIcon } from '../../components/icons';
import { IWorkflowsFiltersProps } from '../../components/Workflows/types';
import {
  canFilterByCurrentPerformer,
  canFilterByTemplateStep,
  checkSortingIsIncorrect,
  getSortingsByStatus,
} from '../../utils/workflows/filters';
import { isArrayWithItems } from '../../utils/helpers';

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
  setTemplatesFilter,
  setStepsFilter,
  removeWorkflowFromList,
  loadTemplateSteps,
  updateCurrentPerformersCounters,
  updateWorkflowsTemplateStepsCounters,
  updateWorkflowStartersCounters,
}: IWorkflowsLayoutComponentProps) {
  const { formatMessage } = useIntl();
  const [isLoadSteps, setIsLoadSteps] = useState(false);

  useEffect(() => {
    setIsLoadSteps(false);
  }, [templatesIdsFilter])

  useEffect(() => {
    if (workflowsView !== EWorkflowsView.Table) {
      return;
    }

    const currentTemplateId = templatesIdsFilter[0];
    if (!currentTemplateId) {
      return;
    }

    const currentTemplate = filterTemplates.find((t) => t.id === currentTemplateId);
    if (!currentTemplate) {
      return;
    }

    if (isArrayWithItems(currentTemplate.steps)) {
      if (!isArrayWithItems(stepsIdsFilter)) {
        setStepsFilter(currentTemplate.steps.map((s) => s.id));
      }

      return;
    }

    if (!isLoadSteps) {
      loadTemplateSteps({
        templateId: currentTemplateId,
        onAfterLoaded: (steps) => {
          if (!isArrayWithItems(stepsIdsFilter)) {
            setStepsFilter(steps.map((s) => s.id));
          }

          if (canFilterByTemplateStep(statusFilter)) {
            updateWorkflowsTemplateStepsCounters();
          }

          setIsLoadSteps(true);
        },
      });
    }
  }, [workflowsView, templatesIdsFilter[0], filterTemplates, statusFilter, isLoadSteps]);


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
  }, [
    statusFilter,
    templatesIdsFilter,
    stepsIdsFilter,
    performersIdsFilter,
    workflowStartersIdsFilter,
    sorting,
  ]);

  useEffect(() => {
    if (checkSortingIsIncorrect(statusFilter, sorting)) {
      changeWorkflowsSorting(EWorkflowsSorting.DateDesc);
    }
  }, [sorting, statusFilter]);

  const templateIdFilter = React.useMemo(() => {
    const [firstTemplate] = templatesIdsFilter;

    return firstTemplate || null;
  }, [templatesIdsFilter[0]]);

  const statusTitles = React.useMemo(() => Object.values(EWorkflowsStatus), []);
  const sortingTitles = React.useMemo(() => getSortingsByStatus(statusFilter), [statusFilter]);

  const renderLeftContent = () => {
    return (
      <div className={styles['navbar-left-content']}>
        <div className={styles['filters']}>
          <Tabs
            activeValueId={workflowsView}
            values={[
              {
                id: EWorkflowsView.Table,
                label: formatMessage({ id: 'workflows.table-view' }),
              },
              {
                id: EWorkflowsView.Grid,
                label: formatMessage({ id: 'workflows.grid-view' }),
              },
            ]}
            onChange={setWorkflowsView}
          />

          {workflowsView === EWorkflowsView.Table && renderFilters()}
        </div>
      </div>
    );
  };

  const renderFilters = () => {
    return (
      <>
        <FilterSelect
          isSearchShown
          noValueLabel={formatMessage({ id: 'sorting.all-templates' })}
          placeholderText={formatMessage({ id: 'sorting.no-template-found' })}
          selectedOption={templateIdFilter}
          options={filterTemplates}
          optionIdKey="id"
          optionLabelKey="name"
          onChange={(templateId: number) => {
            setStepsFilter([]);
            setTemplatesFilter([templateId]);
          }}
          resetFilter={() => {
            setStepsFilter([]);
            setTemplatesFilter([]);
          }}
          Icon={FilterIcon}
          renderPlaceholder={() => {
            const selectedTemplate = filterTemplates.find((t) => t.id === templateIdFilter);
            return selectedTemplate?.name || formatMessage({ id: 'sorting.all-templates' });
          }}
        />
        <SelectMenu values={statusTitles} activeValue={statusFilter} onChange={setStatusFilter} Icon={FilterIcon} />
        <SelectMenu values={sortingTitles} activeValue={sorting} onChange={changeWorkflowsSorting} />
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
    <>
      <TopNavContainer leftContent={renderLeftContent()} />
      <main>
        <div className="container-fluid">{children}</div>

        <WorkflowModalContainer
          onClose={handleCloseWorkflowLogPopup}
          onWorkflowEnded={() => removeWorkflowFromList({ workflowId })}
          onWorkflowDeleted={() => removeWorkflowFromList({ workflowId })}
          onWorkflowSnoozed={() => removeWorkflowFromList({ workflowId })}
          onWorkflowResumed={() => removeWorkflowFromList({ workflowId })}
        />
      </main>
    </>
  );
}
