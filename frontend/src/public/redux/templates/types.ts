import type {
  ISystemTemplate,
  ITemplateListItem,
  ITemplatesSystemCategories,
  TTaskVariable,
  TTemplateIntegrationStats,
} from '../../types/template';
import type { ETemplatesSorting, TTransformedTask } from '../../types/workflow';

export enum ETemplatesSystemStatus {
  WaitingForAction = 'waiting-for-action',
  Loading = 'loading',
  Searching = 'searching',
  NoTemplates = 'no-templates',
}

export interface ITemplatesSystemSelection {
  count: number;
  offset: number;
  searchText: string;
  category: number | null;
}

export interface ITemplatesSystemList {
  items: ISystemTemplate[];
  selection: ITemplatesSystemSelection;
}

export interface ITemplatesSystem {
  isLoading: boolean;
  categories: ITemplatesSystemCategories[];
  list: ITemplatesSystemList;
  status: ETemplatesSystemStatus;
}

export interface ITemplatesList {
  count: number;
  offset: number;
  items: ITemplateListItem[];
}

export interface ITemplatesStore {
  systemTemplates: ITemplatesSystem;
  isListLoading: boolean;
  templatesList: ITemplatesList;
  templatesListSorting: ETemplatesSorting;
  templatesVariablesMap: { [key in number]: TTaskVariable[] };
  templatesTasksMap: { [key in number]: TTransformedTask[] };
  templatesIntegrationsStats: { [key in number]: TTemplateIntegrationStats };
  isTemplateOwner: undefined | boolean;
}
