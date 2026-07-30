import { IApplicationState } from '../../types/redux';
import { IAiAgent } from '../aiAgents/types';

export const getAiAgentsList = (state: IApplicationState): IAiAgent[] => state.aiAgents.list;

export const getActiveAiAgentsList = (state: IApplicationState): IAiAgent[] =>
  state.aiAgents.list.filter((agent) => agent.isActive);

export const getAiAgentsIsLoading = (state: IApplicationState): boolean => state.aiAgents.isLoading;

export const getAiAgentsEnabled = (state: IApplicationState): boolean => state.aiAgents.isEnabled;

export const getAiAgentsEditModal = (state: IApplicationState) => state.aiAgents.editModal;

export const getAiConnectionState = (state: IApplicationState) => state.aiAgents.connection;

// admins who can connect a provider see the AI Agents section even
// before the feature is switched on for the account
export const getAiAgentsSectionVisible = (state: IApplicationState): boolean =>
  state.aiAgents.isEnabled || state.aiAgents.connection.isAvailable;
