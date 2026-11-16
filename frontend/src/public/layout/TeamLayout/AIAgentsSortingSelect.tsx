import React from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { SelectMenu } from '../../components/UI';
import { aiAgentsSortingValues } from '../../constants/sortings';
import { aiAgentsSortingChanged } from '../../redux/ai/slice';
import type { EAIAgentsSorting } from '../../redux/ai/types';
import { getAIAgentsSorting } from '../../redux/selectors/ai';

export function AIAgentsSortingSelect() {
  const dispatch = useDispatch();
  const sorting = useSelector(getAIAgentsSorting);

  const handleChangeSorting = (value: EAIAgentsSorting) => {
    dispatch(aiAgentsSortingChanged(value));
  };

  return <SelectMenu activeValue={sorting} values={aiAgentsSortingValues} onChange={handleChangeSorting} />;
}
