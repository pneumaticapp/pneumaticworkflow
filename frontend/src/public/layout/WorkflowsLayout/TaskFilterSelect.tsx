import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import styles from './WorkflowsLayout.css';
import {
  cancelCurrentPerformersCounters,
  cancelTemplateTasksCounters,
  setFilterTemplateTasks as setWorkflowsFilterTasks,
} from '../../redux/workflows/slice';
import { FilterSelect, TOptionBase } from '../../components/UI';
import { StepName } from '../../components/StepName';
import { TaskFilterIcon } from '../../components/icons';
import { ITemplateFilterItem, TTemplateStepFilter } from '../../types/workflow';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import { isArrayWithItems } from '../../utils/helpers';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import {
  getWorkflowsStatus,
  getWorkflowTasksApiNamesFilter,
  getWorkflowTemplatesIdsFilter,
} from '../../redux/selectors/workflows';
import { useCheckDevice } from '../../hooks/useCheckDevice';

interface IGroupedTasksValue<TOption extends TOptionBase<'apiName', 'name'>> {
  title: string;
  options: TOption[];
}

type IGroupedTasksMap = Map<number, IGroupedTasksValue<TOptionBase<'apiName', 'name'>>>;

export function TaskFilterSelect({ selectedTemplates }: { selectedTemplates: ITemplateFilterItem[] }) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { isMobile } = useCheckDevice();

  const tasksApiNamesFilter = useSelector(getWorkflowTasksApiNamesFilter);
  const statusFilter = useSelector(getWorkflowsStatus);
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);

  const mustDisableFilter = !isArrayWithItems(templatesIdsFilter) || !canFilterByTemplateStep(statusFilter);

  const groupedSteps: IGroupedTasksMap | null = useMemo(() => {
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
      selectedOptions={tasksApiNamesFilter}
      optionIdKey="apiName"
      optionLabelKey="name"
      options={[]}
      groupedOptions={groupedSteps}
      flatGroupedOptions={flatGroupedOptions}
      onChange={(taskApiNames: string[]) => {
        dispatch(setWorkflowsFilterTasks(taskApiNames));
      }}
      resetFilter={() => {
        dispatch(setWorkflowsFilterTasks([]));
        if (!canFilterByTemplateStep(statusFilter)) {
          dispatch(cancelCurrentPerformersCounters());
          dispatch(cancelTemplateTasksCounters());
        }
      }}
      Icon={TaskFilterIcon}
      renderPlaceholder={() =>
        getRenderPlaceholder({
          isDisabled: mustDisableFilter,
          filterIds: tasksApiNamesFilter,
          options: flatGroupedOptions,
          formatMessage,
          type: ERenderPlaceholderType.Task,
          severalOptionPlaceholder: 'sorting.several-tasks',
          defaultPlaceholder: 'sorting.all-tasks',
        })
      }
      containerClassname={styles['filter-container']}
      arrowClassName={styles['header-filter__arrow']}
      positionFixed={isMobile}
    />
  );
}
