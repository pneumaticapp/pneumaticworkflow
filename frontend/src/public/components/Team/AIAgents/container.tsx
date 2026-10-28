import * as React from 'react';
import type { ComponentType } from 'react';
import { useSelector } from 'react-redux';

import { withSyncedQueryString } from '../../../HOCs/withSyncedQueryString';
import { aiAgentsSortingChanged } from '../../../redux/ai/slice';
import { EAIAgentsSorting } from '../../../redux/ai/types';
import { getAIAgentsSorting } from '../../../redux/selectors/ai';
import { AIAgents } from './AIAgents';
import type { IAIAgentsSortingSyncProps } from './types';
import { parseAIAgentsSorting } from './utils/parseAIAgentsSorting';

const AIAgentsSortingSync = () => <AIAgents />;

const SyncedAIAgents = withSyncedQueryString<IAIAgentsSortingSyncProps>([
  {
    propName: 'agentsSorting',
    queryParamName: 'sorting-agent',
    defaultAction: aiAgentsSortingChanged(EAIAgentsSorting.NameAsc),
    createAction: (value) => aiAgentsSortingChanged(parseAIAgentsSorting(value)),
    getQueryParamByProp: (value) => value,
  },
])(AIAgentsSortingSync) as ComponentType<IAIAgentsSortingSyncProps>;

export function AIAgentsContainer() {
  const agentsSorting = useSelector(getAIAgentsSorting);

  return <SyncedAIAgents agentsSorting={agentsSorting} />;
}
