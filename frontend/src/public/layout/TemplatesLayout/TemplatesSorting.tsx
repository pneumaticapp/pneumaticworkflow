import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Select } from '../../components/UI';
import { getTemplatesListSorting } from '../../redux/selectors/templates';
import { changeTemplatesSorting } from '../../redux/actions';
import { workflowsSortingValues } from '../../constants/sortings';
import { getEnumSelectProps } from '../../utils/getEnumSelectProps';

export function TemplatesSorting() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getTemplatesListSorting);

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      {...getEnumSelectProps(
        workflowsSortingValues,
        sorting,
        (value) => dispatch(changeTemplatesSorting(value)),
        formatMessage,
      )}
    />
  );
}
