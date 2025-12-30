import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { setFilterTemplate as setWorkflowsFilterTemplate } from '../../redux/workflows/slice';

import { FilterSelect } from '../../components/UI';
import { FilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import styles from './WorkflowsLayout.css';
import { getWorkflowTemplateListItems, getWorkflowTemplatesIdsFilter } from '../../redux/selectors/workflows';

export function TemplateFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);
  const filterTemplates = useSelector(getWorkflowTemplateListItems);

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
      />
    </div>
  );
}
