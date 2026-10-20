import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import {
  cancelCurrentPerformersCounters,
  cancelTemplateFilterRequests,
  cancelTemplateTasksCounters,
  setFilterTemplate as setWorkflowsFilterTemplate,
} from '../../redux/workflows/slice';

import { Select } from '../../components/UI/Select';
import { FilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import styles from './WorkflowsLayout.css';

import {
  getWorkflowsStatus,
  getWorkflowTemplateListIsLoading,
  getWorkflowTemplateListItems,
  getWorkflowTemplatesIdsFilter,
} from '../../redux/selectors/workflows';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import { useMobileMenuPortalProps } from './useMobileMenuPortalProps';

export function TemplateFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);
  const filterTemplates = useSelector(getWorkflowTemplateListItems);
  const areFilterTemplatesLoading = useSelector(getWorkflowTemplateListIsLoading);
  const statusFilter = useSelector(getWorkflowsStatus);

  const menuPortalProps = useMobileMenuPortalProps();

  const templatesOptions = useMemo(() => {
    return filterTemplates.map(({ count, ...rest }) => ({
      ...rest,
      value: String(rest.id),
      label: rest.name,
      ...(count > 0 && { count }),
    }));
  }, [filterTemplates]);

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      Icon={FilterIcon}
      isMulti
      isSearchable
      isLoading={areFilterTemplatesLoading}
      title={getRenderPlaceholder({
        filterIds: templatesIdsFilter,
        options: templatesOptions,
        formatMessage,
        type: ERenderPlaceholderType.Template,
        severalOptionPlaceholder: 'sorting.several-templates',
        defaultPlaceholder: 'sorting.all-templates',
      })}
      placeholder={formatMessage({ id: 'sorting.search-placeholder' })}
      noOptionsMessage={() => formatMessage({ id: 'sorting.no-template-found' })}
      options={templatesOptions}
      value={templatesOptions.filter((option) => templatesIdsFilter.includes(option.id))}
      onChange={(selected: typeof templatesOptions) => {
        sessionStorage.setItem('isInternalNavigation', 'true');
        dispatch(setWorkflowsFilterTemplate(selected.map((option) => option.id)));
      }}
      onClear={() => {
        sessionStorage.setItem('isInternalNavigation', 'true');
        dispatch(setWorkflowsFilterTemplate([]));
        dispatch(cancelTemplateFilterRequests());
        if (!canFilterByTemplateStep(statusFilter)) {
          dispatch(cancelCurrentPerformersCounters());
          dispatch(cancelTemplateTasksCounters());
        }
      }}
      classNames={{ menuList: () => styles['wide-filter-menu'] }}
      {...menuPortalProps}
    />
  );
}
