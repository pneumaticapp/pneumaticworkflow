import { IApplicationState } from '../../types/redux';
import { ITemplate, IExtraField, ITemplateTask, IKickoff } from '../../types/template';

export const getTemplateData = (state: IApplicationState): ITemplate => {
  return state.template.data;
};

export const getTemplateStatus = (state: IApplicationState) => state.template.status;

export const getKickoff = (state: IApplicationState): IKickoff =>
  state.template.data.kickoff;

export const getKickoffFields = (state: IApplicationState): IExtraField[] =>
  state.template.data.kickoff.fields;

export const getTemplateTasks = (state: IApplicationState): ITemplateTask[] =>
  state.template.data.tasks;
