import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { DropdownList } from '../../components/UI';
import { getTemplatesListSorting } from '../../redux/selectors/templates';
import { changeTemplatesSorting } from '../../redux/actions';
import { workflowsSortingValues } from '../../constants/sortings';
import { getSortingSelectProps } from '../../utils/getSortingSelectProps';

export function TemplatesSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getTemplatesListSorting);

  return (
    <DropdownList
      controlSize="sm"
      controlVariant="accent"
      {...getSortingSelectProps(
        workflowsSortingValues,
        sorting,
        (value) => dispatch(changeTemplatesSorting(value)),
        formatMessage,
      )}
    />
  );
}
