import { EAIAgentsSorting } from '../../../../redux/ai/types';

const AGENTS_SORTINGS: string[] = Object.values(EAIAgentsSorting);

export const parseAIAgentsSorting = (value: string): EAIAgentsSorting =>
  AGENTS_SORTINGS.includes(value) ? (value as EAIAgentsSorting) : EAIAgentsSorting.NameAsc;
