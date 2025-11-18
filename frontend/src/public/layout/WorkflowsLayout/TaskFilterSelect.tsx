import React from 'react';
import { useIntl } from 'react-intl';

import { useDispatch, useSelector } from 'react-redux';
import { IApplicationState } from '../../types/redux';

import styles from './WorkflowsLayout.css';
import { setWorkflowsFilterSteps } from '../../redux/actions';
import { FilterSelect } from '../../components/UI';
import { StepName } from '../../components/StepName';
import { TaskFilterIcon } from '../../components/icons';
// import { isArrayWithItems } from '../../utils/helpers';
// import { canFilterByTemplateStep } from '../../utils/workflows/filters';

export function TaskFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const {
    stepsIdsFilter,
    templatesIdsFilter,
    // statusFilter
  } = useSelector((state: IApplicationState) => state.workflows.workflowsSettings.values);
  const filterTemplates = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.templateList.items,
  );

  const STEP_HEADER_NAME = formatMessage({ id: 'workflows.filter-column-step' });
  //   if (!isArrayWithItems(templatesIdsFilter) || !canFilterByTemplateStep(statusFilter)) {
  //     return STEP_HEADER_NAME;
  //   }

  const [templateIdFilter] = templatesIdsFilter;
  const currentTemplate = filterTemplates.find((t) => t.id === templateIdFilter);
  //   if (!currentTemplate) {
  //     return STEP_HEADER_NAME;
  //   }

  const stepsOptions = currentTemplate?.steps
    ?.map((step: any) => {
      return {
        ...step,
        name: <StepName initialStepName={step.name} templateId={currentTemplate?.id} />,
        subTitle: String(step.number).padStart(2, '0'),
        searchByText: step.name,
      };
    })
    ?.filter((step: any) => step.count);

  return (
    <FilterSelect
      isMultiple
      isSearchShown
      placeholderText={formatMessage({ id: 'workflows.filter-no-step' })}
      searchPlaceholder={formatMessage({ id: 'sorting.search-placeholder' })}
      selectedOptions={stepsIdsFilter}
      optionIdKey="id"
      optionLabelKey="name"
      options={stepsOptions || []}
      onChange={(steps: number[]) => {
        dispatch(setWorkflowsFilterSteps(steps));
      }}
      resetFilter={() => {
        dispatch(setWorkflowsFilterSteps([]));
      }}
      Icon={TaskFilterIcon}
      renderPlaceholder={() => <span className={styles['header-filter']}>{STEP_HEADER_NAME}</span>}
      containerClassname={styles['filter-container']}
      arrowClassName={styles['header-filter__arrow']}
      selectAllLabel={formatMessage({ id: 'workflows.filter-all-steps' })}
    />
  );
}
