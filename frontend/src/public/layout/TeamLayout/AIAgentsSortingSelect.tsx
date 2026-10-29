import React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Select } from '../../components/UI';
import { aiAgentsSortingValues } from '../../constants/sortings';
import { aiAgentsSortingChanged } from '../../redux/ai/slice';
import type { EAIAgentsSorting } from '../../redux/ai/types';
import { getAIAgentsSorting } from '../../redux/selectors/ai';
import { getEnumSelectProps } from '../../utils/getEnumSelectProps';

export function AIAgentsSortingSelect() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const sorting = useSelector(getAIAgentsSorting);

  const handleChangeSorting = (value: EAIAgentsSorting) => {
    dispatch(aiAgentsSortingChanged(value));
  };

  return (
    <Select
      controlSize="sm"
      controlVariant="accent"
      {...getEnumSelectProps(aiAgentsSortingValues, sorting, handleChangeSorting, formatMessage)}
    />
  );
}
