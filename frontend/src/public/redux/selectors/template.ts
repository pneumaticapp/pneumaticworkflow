import { IApplicationState } from '../../types/redux';
import { ITemplateClient, IExtraField, ITemplateTaskClient, ITemplateKickoffClient } from '../../types/template';

export const getTemplateData = (state: IApplicationState): ITemplateClient => {
  return state.template.data;
};

export const getTemplateStatus = (state: IApplicationState) => state.template.status;

export const getAITemplate = (state: IApplicationState) => state.template.AITemplate.generatedData;

export const getKickoff = (state: IApplicationState): ITemplateKickoffClient =>
  state.template.data.kickoff;

export const getKickoffFields = (state: IApplicationState): IExtraField[] => state.template.data.kickoff.fields;

export const getTemplateTasks = (state: IApplicationState): ITemplateTaskClient[] => state.template.data.tasks;
