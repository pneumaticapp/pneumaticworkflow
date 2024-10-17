/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';

import { ITemplate, ITemplateTask } from '../../types/template';
import { ETemplateStatus, ITemplateStore } from '../../types/redux';
import { getEmptyKickoff } from '../../utils/template';

import { ETemplateActions, TTemplateActions } from './actions';

export const initialTemplate: ITemplateStore = {
  data: {
    tasks: [] as ITemplateTask[],
    kickoff: getEmptyKickoff(),
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
  } as ITemplate,
  status: ETemplateStatus.Saved,
  AITemplate: {
    isModalOpened: false,
    generationStatus: 'initial',
    generatedData: null,
  },
};

export const reducer = (state = initialTemplate, action: TTemplateActions): ITemplateStore => {
  switch (action.type) {
    case ETemplateActions.Load:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.Loading;
      });
    case ETemplateActions.LoadFromSystem:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.Loading;
      });
    case ETemplateActions.LoadFromSystemSuccess:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.Saved;
      });
    case ETemplateActions.Save:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.Saving;
      });
    case ETemplateActions.SaveSuccess:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.Saved;
      });
    case ETemplateActions.SaveFailed:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.SaveFailed;
      });
    case ETemplateActions.SaveCanceled:
      return produce(state, (draftState) => {
        draftState.status = ETemplateStatus.SaveCanceled;
      });
    case ETemplateActions.SetTemplate:
      return produce(state, (draftState) => {
        draftState.data = action.payload;
      });
    case ETemplateActions.ResetTemplateStore:
      return initialTemplate;
    case ETemplateActions.SetTemplateStatus:
      return produce(state, (draftState) => {
        draftState.status = action.payload;
      });
    case ETemplateActions.SetIsAITemplateModalOpened:
      return produce(state, (draftState) => {
        draftState.AITemplate.isModalOpened = action.payload;
      });
    case ETemplateActions.SetAITemplateGenerationStatus:
      return produce(state, (draftState) => {
        draftState.AITemplate.generationStatus = action.payload;
      });
    case ETemplateActions.SetAITemplateData:
      return produce(state, (draftState) => {
        draftState.AITemplate.generatedData = action.payload.template;
      });

    default:
      return { ...state };
  }
};
