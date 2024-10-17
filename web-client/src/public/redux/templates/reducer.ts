/* eslint-disable @typescript-eslint/default-param-last */
/* eslint-disable no-param-reassign */
import produce from 'immer';
import { ITemplatesList, ITemplatesStore, ITemplatesSystem, ITemplatesSystemList } from '../../types/redux';
import { ETemplatesActions, ETemplatesSystemStatus, TTemplatesActions } from './actions';
import { TWorkflowsActions } from '../actions';
import { ETemplatesSorting } from '../../types/workflow';
import { omit } from '../../utils/helpers';

const INIT_TEMPLATES_LIST: ITemplatesList = {
  count: -1,
  offset: 0,
  items: [],
};

const INIT_SYSTEM_TEMPLATES_LIST: ITemplatesSystemList = {
  items: [],
  selection: {
    count: -1,
    offset: 0,
    searchText: '',
    category: null,
  },
};

const INIT_SYSTEM_TEMPLATES: ITemplatesSystem = {
  isLoading: false,
  status: ETemplatesSystemStatus.WaitingForAction,
  categories: [],
  list: INIT_SYSTEM_TEMPLATES_LIST,
};

export const INIT_STATE: ITemplatesStore = {
  systemTemplates: INIT_SYSTEM_TEMPLATES,
  isListLoading: false,
  templatesList: INIT_TEMPLATES_LIST,
  templatesListSorting: ETemplatesSorting.DateDesc,
  templatesVariablesMap: {},
  templatesIntegrationsStats: {},
};

export const reducer = (state = INIT_STATE, action: TTemplatesActions | TWorkflowsActions): ITemplatesStore => {
  switch (action.type) {
    case ETemplatesActions.SetCurrentTemplatesSystemStatus:
      return produce(state, (draftState) => {
        draftState.systemTemplates.status = action.payload;
      });
    case ETemplatesActions.LoadTemplatesSystem:
      return produce(state, (draftState) => {
        draftState.systemTemplates.status = ETemplatesSystemStatus.Loading;
        draftState.systemTemplates.isLoading = true;
      });
    case ETemplatesActions.ChangeTemplatesSystem:
      return produce(state, (draftState) => {
        draftState.systemTemplates.isLoading = false;
        draftState.systemTemplates.list.selection.count = action.payload.count;
        draftState.systemTemplates.list.items = action.payload.items;
      });
    case ETemplatesActions.LoadTemplatesSystemFailed:
      return produce(state, (draftState) => {
        draftState.systemTemplates.isLoading = false;
      });
    case ETemplatesActions.ChangeTemplatesSystemSelectionSearch:
      return produce(state, (draftState) => {
        draftState.systemTemplates.status = ETemplatesSystemStatus.Searching;
        draftState.systemTemplates.isLoading = true;
        draftState.systemTemplates.list.selection.searchText = action.payload;
        draftState.systemTemplates.list.selection.offset = 0;
      });
    case ETemplatesActions.ChangeTemplatesSystemSelectionCategory:
      return produce(state, (draftState) => {
        draftState.systemTemplates.status = ETemplatesSystemStatus.Searching;
        draftState.systemTemplates.isLoading = true;
        draftState.systemTemplates.list.selection.category = action.payload;
        draftState.systemTemplates.list.selection.offset = 0;
      });
    case ETemplatesActions.ChangeTemplatesSystemPaginationNext:
      return produce(state, (draftState) => {
        draftState.systemTemplates.isLoading = true;
        draftState.systemTemplates.list.selection.offset = state.systemTemplates.list.selection.offset + 1;
      });
    case ETemplatesActions.ChangeTemplatesSystemCategories:
      return produce(state, (draftState) => {
        draftState.systemTemplates.categories = action.payload;
      });
    case ETemplatesActions.ResetTemplates: {
      return {
        ...state,
        templatesList: INIT_TEMPLATES_LIST,
      };
    }
    case ETemplatesActions.LoadTemplates:
      return { ...state, isListLoading: true };
    case ETemplatesActions.LoadTemplatesFailed:
      return { ...state, isListLoading: false };
    case ETemplatesActions.ChangeTemplatesList:
      return { ...state, isListLoading: false, templatesList: action.payload };
    case ETemplatesActions.ChangeTemplatesListSorting:
      return { ...state, isListLoading: false, templatesListSorting: action.payload };
    case ETemplatesActions.LoadTemplateVariablesSuccess: {
      return produce(state, (draftState) => {
        const { templateId, variables } = action.payload;
        const oldVariables = (draftState.templatesVariablesMap[templateId] || []).filter(
          (ov) => !variables.some((v) => ov.apiName === v.apiName),
        );
        draftState.templatesVariablesMap[templateId] = [...variables, ...oldVariables];
      });
    }
    case ETemplatesActions.SetTemplateIntegrationsStats: {
      const templatesIntegrationsStats = action.payload.reduce((acc, item) => {
        return { ...acc, [item.id]: omit(item, ['id']) };
      }, state.templatesIntegrationsStats);

      return { ...state, templatesIntegrationsStats };
    }

    default:
      return { ...state };
  }
};
