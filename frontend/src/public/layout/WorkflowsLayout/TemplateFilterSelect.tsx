import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import { setWorkflowsFilterSteps, setWorkflowsFilterTemplate } from '../../redux/actions';
import { IApplicationState } from '../../types/redux';

import { FilterSelect } from '../../components/UI';
import { FilterIcon } from '../../components/icons';
import { ERenderPlaceholderType, getRenderPlaceholder } from './utils';
import styles from './WorkflowsLayout.css';

export function TemplateFilterSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { templatesIdsFilter } = useSelector((state: IApplicationState) => state.workflows.workflowsSettings.values);
  const { items: filterTemplates } = useSelector(
    (state: IApplicationState) => state.workflows.workflowsSettings.templateList,
  );

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
          dispatch(setWorkflowsFilterSteps([])); // change after addiing the new task filter
          dispatch(setWorkflowsFilterTemplate(templateIds));
        }}
        resetFilter={() => {
          sessionStorage.setItem('isInternalNavigation', 'true');
          dispatch(setWorkflowsFilterSteps([]));
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
        selectAllLabel={formatMessage({ id: 'workflows.filter-all-templates' })}
      />
    </div>
  );
}
