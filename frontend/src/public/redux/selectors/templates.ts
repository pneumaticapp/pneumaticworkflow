import { TTaskVariable } from '../../components/TemplateEdit/types';
import { ITemplatesList, ITemplatesStore, ITemplatesSystem, ITemplatesSystemList } from '../../types/redux';
import type { RootState } from '../store';
import { TTransformedTask } from '../../types/template';
import { ETemplatesSorting } from '../../types/workflow';

export const getTemplatesStore = (state: RootState): ITemplatesStore => state.templates;

export const getTemplatesList = (state: RootState): ITemplatesList => state.templates.templatesList;

export const getTemplatesIsListLoading = (state: RootState): boolean => state.templates.isListLoading;

export const getTemplatesListSorting = (state: RootState): ETemplatesSorting => state.templates.templatesListSorting;

export const getTemplatesSystem = (state: RootState): ITemplatesSystem => state.templates.systemTemplates;

export const getTemplatesSystemList = (state: RootState): ITemplatesSystemList => state.templates.systemTemplates.list;

export const getTemplatesIntegrationsStats = (state: RootState) => state.templates.templatesIntegrationsStats;

export const getTemplatesTasks =
  (templateId: number) =>
  (state: RootState): TTransformedTask[] =>
    state.templates.templatesTasksMap[templateId];

export const getTemplatesVariables =
  (templateId: number) =>
  (state: RootState): TTaskVariable[] =>
    state.templates.templatesVariablesMap[templateId];
