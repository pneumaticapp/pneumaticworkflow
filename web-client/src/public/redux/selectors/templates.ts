import { IApplicationState, ITemplatesList, ITemplatesStore, ITemplatesSystemList } from '../../types/redux';

export const getTemplatesList = (state: IApplicationState): ITemplatesList => state.templates.templatesList;

export const getTemplatesStore = (state: IApplicationState): ITemplatesStore => state.templates;

export const getTemplatesSystemList = (state: IApplicationState): ITemplatesSystemList =>
  state.templates.systemTemplates.list;

export const getTemplatesIntegrationsStats = (state: IApplicationState) => state.templates.templatesIntegrationsStats;
