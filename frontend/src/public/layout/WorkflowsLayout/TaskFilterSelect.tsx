import React, { ReactNode, useMemo } from 'react';
import { useIntl } from 'react-intl';

import { useDispatch, useSelector } from 'react-redux';
import { IApplicationState } from '../../types/redux';

import styles from './WorkflowsLayout.css';
import { setWorkflowsFilterSteps } from '../../redux/actions';
import { FilterSelect } from '../../components/UI';
import { StepName } from '../../components/StepName';
import { TaskFilterIcon } from '../../components/icons';
import { ITemplateFilterItem, TTemplateStepFilter } from '../../types/workflow';
// import { isArrayWithItems } from '../../utils/helpers';
// import { canFilterByTemplateStep } from '../../utils/workflows/filters';

interface TStepOptionFilter extends Omit<TTemplateStepFilter, 'name' | 'number'> {
  name: ReactNode;
  subTitle: string;
  searchByText: string;
  count?: number;
}

export interface IGroupedStepsValue {
  title: string;
  options: TStepOptionFilter[];
}

type IGroupedStepsMap = Map<number, IGroupedStepsValue>;

export function TaskFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const {
    stepsIdsFilter,
    // statusFilter
    templatesIdsFilter,
  }: {
    stepsIdsFilter: number[];
    // statusFilter
    templatesIdsFilter: number[];
  } = useSelector((state: IApplicationState) => state.workflows.workflowsSettings.values);

  const filterTemplates: ITemplateFilterItem[] = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.templateList.items,
  );

  const groupedSteps: IGroupedStepsMap | null = useMemo(() => {
    if (templatesIdsFilter.length === 0) {
      return null;
    }
    const filterTemplatesMap: Map<number, ITemplateFilterItem> = new Map(
      filterTemplates.map((template) => [template.id, template]),
    );

    const selectedTemplates: ITemplateFilterItem[] = templatesIdsFilter
      .map((templateId) => filterTemplatesMap.get(templateId))
      .filter(Boolean) as ITemplateFilterItem[];

    return new Map(
      selectedTemplates.map((template) => [
        template.id,
        {
          title: template.name,
          options: template.steps.map(({ name, number, count, ...rest }: TTemplateStepFilter) => ({
            ...rest,
            name: <StepName initialStepName={name} templateId={template.id} />,
            subTitle: String(number).padStart(2, '0'),
            searchByText: name,
            ...(count && { count }),
          })),
        },
      ]),
    );
  }, [templatesIdsFilter, filterTemplates]);

  const STEP_HEADER_NAME = formatMessage({ id: 'workflows.filter-column-step' });
  //   if (!isArrayWithItems(templatesIdsFilter) || !canFilterByTemplateStep(statusFilter)) {
  //     return STEP_HEADER_NAME;
  //   }

  return (
    <FilterSelect
      isMultiple
      isSearchShown
      placeholderText={formatMessage({ id: 'workflows.filter-no-step' })}
      searchPlaceholder={formatMessage({ id: 'sorting.search-placeholder' })}
      selectedOptions={stepsIdsFilter}
      optionIdKey="id"
      optionLabelKey="name"
      options={[]}
      groupedOptions={groupedSteps}
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
    />
  );
}
