import type { IAIAgent } from '../../../api/ai/types';

export interface ITeamAgentProps {
  agent: IAIAgent;
  providerName?: string;
}

export interface IEditAIAgentModalProps {
  agent: IAIAgent;
  onClose(): void;
}

export interface IAgentAvatarProps {
  name: string;
  photo?: string | null;
  size: 'md' | 'lg';
}
