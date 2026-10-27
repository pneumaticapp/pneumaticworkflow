import type { IAIAgent } from '../../../api/ai/types';

export interface ITeamAgentProps {
  agent: IAIAgent;
  providerName?: string;
}

export interface IEditAIAgentModalProps {
  agent: IAIAgent;
  onClose(): void;
}
