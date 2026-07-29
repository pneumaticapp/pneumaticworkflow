import { IApplicationState } from '../../types/redux';
import { ITemplateClient, ITemplateTaskClient, IKickoffClient, IExtraField } from '../../types/template';

export const getTemplateData = (state: IApplicationState): ITemplateClient => {
  return state.template.data;
};

export const getTemplateStatus = (state: IApplicationState) => state.template.status;

export const getKickoff = (state: IApplicationState): IKickoffClient =>
  state.template.data.kickoff;

export const getKickoffFields = (state: IApplicationState): IExtraField[] =>
  state.template.data.kickoff.fields;

export const getTemplateTasks = (state: IApplicationState): ITemplateTaskClient[] =>
  state.template.data.tasks;
