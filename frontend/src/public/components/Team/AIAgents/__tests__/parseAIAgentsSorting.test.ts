import { parseAIAgentsSorting } from '../utils/parseAIAgentsSorting';
import { EAIAgentsSorting } from '../../../../redux/ai/types';

describe('parseAIAgentsSorting', () => {
  it('keeps a known sorting', () => {
    expect(parseAIAgentsSorting(EAIAgentsSorting.DateDesc)).toBe(EAIAgentsSorting.DateDesc);
  });

  it('falls back to name A-Z for an unknown query value', () => {
    expect(parseAIAgentsSorting('random')).toBe(EAIAgentsSorting.NameAsc);
  });
});
