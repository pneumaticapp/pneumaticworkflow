/* eslint-disable */
/* prettier-ignore */
import { ETemplateStatus, ITypedReduxAction } from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { ITemplate, ITemplateTask, TAITemplateGenerationStatus } from '../../types/template';

export const enum ETemplateActions {
  Load = 'LOAD_TEMPLATE',
  LoadFromSystem = 'LOAD_TEMPLATE_FROM_SYSTEM_TEMPLATE',
  ResetTemplateStore = 'RESET_TEMPLATE_STORE',
  Save = 'SAVE_TEMPLATE',
  LoadFromSystemSuccess = 'LOAD_TEMPLATE_FROM_SYSTEM_TEMPLATE_SUCCESS',
  SaveSuccess = 'SAVE_TEMPLATE_SUCCESS',
  SaveFailed = 'SAVE_TEMPLATE_FAILED',
  SaveCanceled = 'SAVE_TEMPLATE_CANCELED',
  SetTemplate = 'SET_TEMPLATE',
  SetTemplateStatus = 'SET_TEMPLATE_STATUS',
  PatchTemplate = 'PATCH_TEMPLATE',
  PatchTask = 'PATCH_TASK',
  CloneTemplate = 'CLONE_TEMPLATE',
  DeleteTemplate = 'DELETE_TEMPLATE',
  SetIsAITemplateModalOpened = 'SET_IS_AI_TEMPLATE_MODAL_OPENED',
  SetAITemplateGenerationStatus = 'SET_AI_TEMPLATE_GENERATION_STATUS',
  SetAITemplateData = 'SET_AI_TEMPLATE_DATA',
  GenerateAITemplate = 'GENERATE_AI_TEMPLATE',
  StopAITemplateGeneration = 'STOP_AI_TEMPLATE_GENERATION',
  ApplyAITemplate = 'APPLY_AI_TEMPLATE',
  DiscardChanges = 'DISCARD_TEMPLATE_CHANGES',
}

export type TLoadTemplate = ITypedReduxAction<ETemplateActions.Load, number>;
export const loadTemplate: (payload: number) => TLoadTemplate = actionGenerator<ETemplateActions.Load, number>(
  ETemplateActions.Load,
);

export type TSetTemplate = ITypedReduxAction<ETemplateActions.SetTemplate, ITemplate>;
export const setTemplate: (payload: ITemplate) => TSetTemplate = actionGenerator<
  ETemplateActions.SetTemplate,
  ITemplate
>(ETemplateActions.SetTemplate);

export type TLoadTemplateFromSystem = ITypedReduxAction<ETemplateActions.LoadFromSystem, string>;
export const loadTemplateFromSystem: (payload: string) => TLoadTemplateFromSystem = actionGenerator<
  ETemplateActions.LoadFromSystem,
  string
>(ETemplateActions.LoadFromSystem);

export type TReseTemplateStore = ITypedReduxAction<ETemplateActions.ResetTemplateStore, void>;
export const resetTemplateStore: (payload?: void) => TReseTemplateStore = actionGenerator<
  ETemplateActions.ResetTemplateStore,
  void
>(ETemplateActions.ResetTemplateStore);

export type TSaveTemplatePayload =
  | {
      onSuccess?(): void;
      onFailed?(): void;
    }
  | undefined;
export type TSaveTemplate = ITypedReduxAction<ETemplateActions.Save, TSaveTemplatePayload>;
export const saveTemplate: (payload?: TSaveTemplatePayload) => TSaveTemplate = actionGenerator<
  ETemplateActions.Save,
  TSaveTemplatePayload
>(ETemplateActions.Save);

export type TLoadFromSystemSuccess = ITypedReduxAction<ETemplateActions.LoadFromSystemSuccess, void>;
export const loadFromSystemSuccess: (payload?: void) => TLoadFromSystemSuccess = actionGenerator<
  ETemplateActions.LoadFromSystemSuccess,
  void
>(ETemplateActions.LoadFromSystemSuccess);

export type TSaveTemplateSuccess = ITypedReduxAction<ETemplateActions.SaveSuccess, void>;
export const saveTemplateSuccess: (payload?: void) => TSaveTemplateSuccess = actionGenerator<
  ETemplateActions.SaveSuccess,
  void
>(ETemplateActions.SaveSuccess);

export type TSaveTemplateFailed = ITypedReduxAction<ETemplateActions.SaveFailed, void>;
export const saveTemplateFailed: (payload?: void) => TSaveTemplateFailed = actionGenerator<
  ETemplateActions.SaveFailed,
  void
>(ETemplateActions.SaveFailed);

export type TSaveTemplateCanceled = ITypedReduxAction<ETemplateActions.SaveCanceled, void>;
export const saveTemplateCanceled: (payload?: void) => TSaveTemplateCanceled = actionGenerator<
  ETemplateActions.SaveCanceled,
  void
>(ETemplateActions.SaveCanceled);

export type TSetTemplateStatus = ITypedReduxAction<ETemplateActions.SetTemplateStatus, ETemplateStatus>;
export const setTemplateStatus: (payload: ETemplateStatus) => TSetTemplateStatus = actionGenerator<
  ETemplateActions.SetTemplateStatus,
  ETemplateStatus
>(ETemplateActions.SetTemplateStatus);

export type TPatchTemplatePayload = {
  changedFields: Partial<ITemplate>;
  onSuccess?(): void;
  onFailed?(): void;
};
export type TPatchTemplate = ITypedReduxAction<ETemplateActions.PatchTemplate, TPatchTemplatePayload>;
export const patchTemplate: (payload: TPatchTemplatePayload) => TPatchTemplate = actionGenerator<
  ETemplateActions.PatchTemplate,
  TPatchTemplatePayload
>(ETemplateActions.PatchTemplate);

export type TPatchTaskPayload = {
  taskUUID: string;
  changedFields: Partial<ITemplateTask>;
};
export type TPatchTask = ITypedReduxAction<ETemplateActions.PatchTask, TPatchTaskPayload>;
export const patchTask: (payload: TPatchTaskPayload) => TPatchTask = actionGenerator<
  ETemplateActions.PatchTask,
  TPatchTaskPayload
>(ETemplateActions.PatchTask);

export type TCloneTemplatePayload = { templateId: number };
export type TCloneTemplate = ITypedReduxAction<ETemplateActions.CloneTemplate, TCloneTemplatePayload>;
export const cloneTemplate: (payload: TCloneTemplatePayload) => TCloneTemplate = actionGenerator<
  ETemplateActions.CloneTemplate,
  TCloneTemplatePayload
>(ETemplateActions.CloneTemplate);

export type TDeleteTemplatePayload = { templateId: number };
export type TDeleteTemplate = ITypedReduxAction<ETemplateActions.DeleteTemplate, TDeleteTemplatePayload>;
export const deleteTemplate: (payload: TDeleteTemplatePayload) => TDeleteTemplate = actionGenerator<
  ETemplateActions.DeleteTemplate,
  TDeleteTemplatePayload
>(ETemplateActions.DeleteTemplate);

export type TSetIsAITemplateModalOpened = ITypedReduxAction<ETemplateActions.SetIsAITemplateModalOpened, boolean>;
export const setIsAITemplateModalOpened: (payload: boolean) => TSetIsAITemplateModalOpened = actionGenerator<
  ETemplateActions.SetIsAITemplateModalOpened,
  boolean
>(ETemplateActions.SetIsAITemplateModalOpened);

export type TSetAITemplateGenerationStatus = ITypedReduxAction<ETemplateActions.SetAITemplateGenerationStatus, TAITemplateGenerationStatus>;
export const setAITemplateGenerationStatus: (payload: TAITemplateGenerationStatus) => TSetAITemplateGenerationStatus = actionGenerator<
  ETemplateActions.SetAITemplateGenerationStatus,
  TAITemplateGenerationStatus
>(ETemplateActions.SetAITemplateGenerationStatus);

export type TSetAITemplateDataPayload = { template: ITemplate | null };
export type TSetAITemplateData = ITypedReduxAction<
  ETemplateActions.SetAITemplateData,
  TSetAITemplateDataPayload
>;
export const setAITemplateData: (payload: TSetAITemplateDataPayload) => TSetAITemplateData = actionGenerator<
  ETemplateActions.SetAITemplateData,
  TSetAITemplateDataPayload
>(ETemplateActions.SetAITemplateData);

export type TGenerateAITemplatePayload = { description: string };
export type TGenerateAITemplate = ITypedReduxAction<
  ETemplateActions.GenerateAITemplate,
  TGenerateAITemplatePayload
>;
export const generateAITemplate: (payload: TGenerateAITemplatePayload) => TGenerateAITemplate = actionGenerator<
  ETemplateActions.GenerateAITemplate,
  TGenerateAITemplatePayload
>(ETemplateActions.GenerateAITemplate);

export type TStopAITemplateGeneration = ITypedReduxAction<
  ETemplateActions.StopAITemplateGeneration,
  void
>;
export const stopAITemplateGeneration: (payload?: void) => TStopAITemplateGeneration = actionGenerator<
  ETemplateActions.StopAITemplateGeneration,
  void
>(ETemplateActions.StopAITemplateGeneration);

export type TApplyAITemplate = ITypedReduxAction<
  ETemplateActions.ApplyAITemplate,
  void
>;
export const applyAITemplate: (payload?: void) => TApplyAITemplate = actionGenerator<
  ETemplateActions.ApplyAITemplate,
  void
>(ETemplateActions.ApplyAITemplate);

type TDiscardChangesPayload = {
  templateId: number;
  onSuccess?(): void; 
}
export type TDiscardChanges = ITypedReduxAction<
  ETemplateActions.DiscardChanges,
  TDiscardChangesPayload
>;
export const discardTemplateChanges: (payload: TDiscardChangesPayload) => TDiscardChanges = actionGenerator<
  ETemplateActions.DiscardChanges,
  TDiscardChangesPayload
>(ETemplateActions.DiscardChanges);

export type TTemplateActions =
  | TLoadTemplate
  | TSetTemplate
  | TLoadTemplateFromSystem
  | TReseTemplateStore
  | TSaveTemplate
  | TSaveTemplateSuccess
  | TSaveTemplateFailed
  | TSaveTemplateCanceled
  | TSetTemplateStatus
  | TPatchTemplate
  | TPatchTask
  | TCloneTemplate
  | TDeleteTemplate
  | TSetIsAITemplateModalOpened
  | TSetAITemplateGenerationStatus
  | TSetAITemplateData
  | TGenerateAITemplate
  | TStopAITemplateGeneration
  | TLoadFromSystemSuccess
  | TApplyAITemplate
  | TDiscardChanges;
