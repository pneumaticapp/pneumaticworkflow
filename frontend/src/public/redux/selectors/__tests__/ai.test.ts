import { getAIAgentsSorted } from '../ai';
import { EAIAgentsSorting } from '../../ai/types';
import type { IApplicationState } from '../../../types/redux';
import type { IAIAgent } from '../../../api/ai/types';

const buildAgent = (id: number, name: string): IAIAgent => ({
  id,
  name,
  photo: null,
  isActive: true,
  providerId: 1,
  model: 'model',
  systemPrompt: 'prompt',
});

const getState = (agentsSorting: EAIAgentsSorting) =>
  ({
    ai: {
      agents: { isLoading: false, list: [buildAgent(1, 'Bravo'), buildAgent(3, 'Alpha'), buildAgent(2, 'Charlie')] },
      agentsSorting,
    },
  }) as unknown as IApplicationState;

const getNames = (agentsSorting: EAIAgentsSorting) =>
  getAIAgentsSorted(getState(agentsSorting)).map(({ name }) => name);

describe('getAIAgentsSorted', () => {
  it('sorts by name A-Z', () => {
    expect(getNames(EAIAgentsSorting.NameAsc)).toEqual(['Alpha', 'Bravo', 'Charlie']);
  });

  it('sorts by name Z-A', () => {
    expect(getNames(EAIAgentsSorting.NameDesc)).toEqual(['Charlie', 'Bravo', 'Alpha']);
  });
});
