import React from 'react';
import { useSelector } from 'react-redux';

import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { changeTemplatesSorting } from '../../redux/actions';
import { getTemplatesListSorting } from '../../redux/selectors/templates';
import { ETemplatesSorting } from '../../types/workflow';
import { Templates } from './Templates';
import { ITemplatesSortingSyncProps } from './types';

const TemplatesSortingSync: React.FC<ITemplatesSortingSyncProps> = () => <Templates />;

const SyncedTemplates = withSyncedQueryString<ITemplatesSortingSyncProps>([
  {
    propName: 'templatesListSorting',
    queryParamName: 'sorting',
    defaultAction: changeTemplatesSorting(ETemplatesSorting.DateDesc),
    createAction: changeTemplatesSorting,
    getQueryParamByProp: (value) => value,
  },
])(TemplatesSortingSync);

export function TemplatesContainer() {
  const templatesListSorting = useSelector(getTemplatesListSorting);
  const SyncedTemplatesComponent = SyncedTemplates as React.ComponentType<ITemplatesSortingSyncProps>;

  return <SyncedTemplatesComponent templatesListSorting={templatesListSorting} />;
}
