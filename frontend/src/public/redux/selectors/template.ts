import type { RootState } from '../store';
import { ITemplateClient, ITemplateTaskClient, ITemplateKickoffClient, IExtraField } from '../../types/template';

export const getTemplateData = (state: RootState): ITemplateClient => {
  return state.template.data;
};

export const getTemplateStatus = (state: RootState) => state.template.status;

export const getKickoff = (state: RootState): ITemplateKickoffClient => state.template.data.kickoff;

export const getKickoffFields = (state: RootState): IExtraField[] => state.template.data.kickoff.fields;

export const getTemplateTasks = (state: RootState): ITemplateTaskClient[] => state.template.data.tasks;
