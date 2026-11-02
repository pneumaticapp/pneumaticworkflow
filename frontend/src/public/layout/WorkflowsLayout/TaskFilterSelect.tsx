import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  cancelCurrentPerformersCounters,
  cancelTemplateTasksCounters,
  setFilterTemplateTasks as setWorkflowsFilterTasks,
} from '../../redux/workflows/slice';
import { Select } from '../../components/UI/Select';
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
import { useMobileMenuPortalProps } from './useMobileMenuPortalProps';

export function TaskFilterSelect({ selectedTemplates }: { selectedTemplates: ITemplateFilterItem[] }) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const menuPortalProps = useMobileMenuPortalProps();

  const tasksApiNamesFilter = useSelector(getWorkflowTasksApiNamesFilter);
  const statusFilter = useSelector(getWorkflowsStatus);
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);

  const mustDisableFilter = !isArrayWithItems(templatesIdsFilter) || !canFilterByTemplateStep(statusFilter);

  const areStepsLoading = selectedTemplates.some((template) => template.areStepsLoading);

  const groupedSteps = useMemo(
    () =>
      selectedTemplates.map((template) => ({
        label: template.name,
        options: template.steps.map(({ name, apiName, count }: TTemplateStepFilter) => {
          const stepName = <StepName initialStepName={name} templateId={template.id} />;

          return {
            apiName,
            value: apiName,
            name: stepName,
            label: stepName,
            searchByText: name,
            ...(count && { count }),
          };
        }),
      })),
    [selectedTemplates],
  );

  const flatGroupedOptions = useMemo(() => groupedSteps.flatMap((group) => group.options), [groupedSteps]);

  const handleClear = () => {
    dispatch(setWorkflowsFilterTasks([]));
    if (!canFilterByTemplateStep(statusFilter)) {
      dispatch(cancelCurrentPerformersCounters());
      dispatch(cancelTemplateTasksCounters());
    }
  };

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      Icon={TaskFilterIcon}
      isMulti
      isSearchable
      isDisabled={mustDisableFilter}
      isLoading={!mustDisableFilter && areStepsLoading}
      title={getRenderPlaceholder({
        isDisabled: mustDisableFilter,
        filterIds: tasksApiNamesFilter,
        options: flatGroupedOptions,
        formatMessage,
        type: ERenderPlaceholderType.Task,
        severalOptionPlaceholder: 'sorting.several-tasks',
        defaultPlaceholder: 'sorting.all-tasks',
      })}
      placeholder={formatMessage({ id: 'sorting.search-placeholder' })}
      noOptionsMessage={() => formatMessage({ id: 'workflows.filter-no-step' })}
      options={groupedSteps}
      value={flatGroupedOptions.filter((option) => tasksApiNamesFilter.includes(option.apiName))}
      onChange={(selected: typeof flatGroupedOptions) => {
        dispatch(setWorkflowsFilterTasks(selected.map((option) => option.apiName)));
      }}
      onClear={tasksApiNamesFilter.length > 0 ? handleClear : undefined}
      {...menuPortalProps}
    />
  );
}
