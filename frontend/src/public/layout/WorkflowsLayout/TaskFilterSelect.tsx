import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import styles from './WorkflowsLayout.css';
import { setFilterTemplateSteps as setWorkflowsFilterSteps } from '../../redux/workflows/slice';
import { FilterSelect, TOptionBase } from '../../components/UI';
import { StepName } from '../../components/StepName';
import { TaskFilterIcon } from '../../components/icons';
import { ITemplateFilterItem, TTemplateStepFilter } from '../../types/workflow';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import { isArrayWithItems } from '../../utils/helpers';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import {
  getWorkflowsStatus,
  getWorkflowStepsIdsFilter,
  getWorkflowTemplatesIdsFilter,
} from '../../redux/selectors/workflows';

export interface IGroupedStepsValue<TOption extends TOptionBase<'id', 'name'>> {
  title: string;
  options: TOption[];
}

export type IGroupedStepsOption = TOptionBase<'id', 'name'> | string;
export type IGroupedStepsMap = Map<number, IGroupedStepsValue<TOptionBase<'id', 'name'>>>;

export function TaskFilterSelect({ selectedTemplates }: { selectedTemplates: ITemplateFilterItem[] }) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const stepsIdsFilter = useSelector(getWorkflowStepsIdsFilter);
  const statusFilter = useSelector(getWorkflowsStatus);
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);

  const mustDisableFilter = !isArrayWithItems(templatesIdsFilter) || !canFilterByTemplateStep(statusFilter);

  const groupedSteps: IGroupedStepsMap | null = useMemo(() => {
    if (selectedTemplates.length === 0) {
      return new Map();
    }
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
  }, [selectedTemplates]);

  const flatGroupedOptions = useMemo(() => {
    return groupedSteps ? Array.from(groupedSteps.values()).flatMap((group) => group.options) : [];
  }, [groupedSteps]);

  return (
    <FilterSelect
      isDisabled={mustDisableFilter}
      isMultiple
      isSearchShown
      placeholderText={formatMessage({ id: 'workflows.filter-no-step' })}
      searchPlaceholder={formatMessage({ id: 'sorting.search-placeholder' })}
      selectedOptions={stepsIdsFilter}
      optionIdKey="id"
      optionLabelKey="name"
      options={[]}
      groupedOptions={groupedSteps}
      flatGroupedOptions={flatGroupedOptions}
      onChange={(taskIds: number[]) => {
        dispatch(setWorkflowsFilterSteps(taskIds));
      }}
      resetFilter={() => {
        dispatch(setWorkflowsFilterSteps([]));
      }}
      Icon={TaskFilterIcon}
      renderPlaceholder={() =>
        getRenderPlaceholder({
          isDisabled: mustDisableFilter,
          filterIds: stepsIdsFilter,
          options: flatGroupedOptions,
          formatMessage,
          type: ERenderPlaceholderType.Task,
          severalOptionPlaceholder: 'sorting.several-tasks',
          defaultPlaceholder: 'sorting.all-tasks',
        })
      }
      containerClassname={styles['filter-container']}
      arrowClassName={styles['header-filter__arrow']}
    />
  );
}
