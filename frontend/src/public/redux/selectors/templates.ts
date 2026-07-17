import { TTaskVariable } from '../../components/TemplateEdit/types';
import {
  IApplicationState,
  ITemplatesList,
  ITemplatesStore,
  ITemplatesSystem,
  ITemplatesSystemList,
} from '../../types/redux';
import { TTransformedTask } from '../../types/template';
import { ETemplatesSorting } from '../../types/workflow';

export const getTemplatesStore = (state: IApplicationState): ITemplatesStore => state.templates;

export const getTemplatesList = (state: IApplicationState): ITemplatesList => state.templates.templatesList;

export const getTemplatesIsListLoading = (state: IApplicationState): boolean => state.templates.isListLoading;

export const getTemplatesListSorting = (state: IApplicationState): ETemplatesSorting =>
  state.templates.templatesListSorting;

export const getTemplatesSystem = (state: IApplicationState): ITemplatesSystem => state.templates.systemTemplates;

export const getTemplatesSystemList = (state: IApplicationState): ITemplatesSystemList =>
  state.templates.systemTemplates.list;

export const getTemplatesIntegrationsStats = (state: IApplicationState) => state.templates.templatesIntegrationsStats;

export const getTemplatesTasks =
  (templateId: number) =>
    (state: IApplicationState): TTransformedTask[] =>
      state.templates.templatesTasksMap[templateId];

export const getTemplatesVariables =
  (templateId: number) =>
    (state: IApplicationState): TTaskVariable[] =>
      state.templates.templatesVariablesMap[templateId];
