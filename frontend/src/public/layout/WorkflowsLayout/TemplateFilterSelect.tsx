import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import {
  cancelCurrentPerformersCounters,
  cancelTemplateFilterRequests,
  cancelTemplateTasksCounters,
  setFilterTemplate as setWorkflowsFilterTemplate,
} from '../../redux/workflows/slice';

import { FilterSelect } from '../../components/UI';
import { FilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import styles from './WorkflowsLayout.css';

import {
  getWorkflowsStatus,
  getWorkflowTemplateListItems,
  getWorkflowTemplatesIdsFilter,
} from '../../redux/selectors/workflows';
import { canFilterByTemplateStep } from '../../utils/workflows/filters';
import { useCheckDevice } from '../../hooks/useCheckDevice';

export function TemplateFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);
  const filterTemplates = useSelector(getWorkflowTemplateListItems);
  const statusFilter = useSelector(getWorkflowsStatus);

  const { isMobile } = useCheckDevice();

  const templatesOptions = useMemo(() => {
    return filterTemplates.map(({ count, ...rest }) => ({
      ...rest,
      ...(count > 0 && { count }),
    }));
  }, [filterTemplates]);

  return (
    <div className={styles['template-filter']}>
      <FilterSelect
        isMultiple
        isSearchShown
        noValueLabel={formatMessage({ id: 'sorting.all-templates' })}
        placeholderText={formatMessage({ id: 'sorting.no-template-found' })}
        searchPlaceholder={formatMessage({ id: 'sorting.search-placeholder' })}
        selectedOptions={templatesIdsFilter}
        options={templatesOptions}
        optionIdKey="id"
        optionLabelKey="name"
        onChange={(templateIds: number[]) => {
          sessionStorage.setItem('isInternalNavigation', 'true');
          dispatch(setWorkflowsFilterTemplate(templateIds));
        }}
        resetFilter={() => {
          sessionStorage.setItem('isInternalNavigation', 'true');
          dispatch(setWorkflowsFilterTemplate([]));
          dispatch(cancelTemplateFilterRequests());
          if (!canFilterByTemplateStep(statusFilter)) {
            dispatch(cancelCurrentPerformersCounters());
            dispatch(cancelTemplateTasksCounters());
          }
        }}
        Icon={FilterIcon}
        renderPlaceholder={() =>
          getRenderPlaceholder({
            filterIds: templatesIdsFilter,
            options: templatesOptions,
            formatMessage,
            type: ERenderPlaceholderType.Template,
            severalOptionPlaceholder: 'sorting.several-templates',
            defaultPlaceholder: 'sorting.all-templates',
          })
        }
        positionFixed={isMobile}
      />
    </div>
  );
}
