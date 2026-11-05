import type { IAIAgent } from '../../../api/ai/types';
import { EAIAgentsSorting } from '../types';

export const aiAgentsComparators: Record<EAIAgentsSorting, (first: IAIAgent, second: IAIAgent) => number> = {
  [EAIAgentsSorting.NameAsc]: (first, second) => first.name.localeCompare(second.name),
  [EAIAgentsSorting.NameDesc]: (first, second) => second.name.localeCompare(first.name),
};
