import { TTaskVariable } from '../../components/TemplateEdit/types';
import { IApplicationState, ITemplatesList, ITemplatesStore, ITemplatesSystemList } from '../../types/redux';
import { TTransformedTask } from '../../types/template';

export const getTemplatesStore = (state: IApplicationState): ITemplatesStore => state.templates;

export const getTemplatesList = (state: IApplicationState): ITemplatesList => state.templates.templatesList;

export const getTemplatesSystemList = (state: IApplicationState): ITemplatesSystemList =>
  state.templates.systemTemplates.list;

export const getTemplatesIntegrationsStats = (state: IApplicationState) => state.templates.templatesIntegrationsStats;

export const getTemplateTasks =
  (templateId: number) =>
    (state: IApplicationState): TTransformedTask[] =>
      state.templates.templatesTasksMap[templateId] || [];

export const getVariables =
  (templateId: number) =>
    (state: IApplicationState): TTaskVariable[] =>
      state.templates.templatesVariablesMap[templateId] || [];
