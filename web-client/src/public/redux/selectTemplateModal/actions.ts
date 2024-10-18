import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { ITemplateListItem } from '../../types/template';

export enum ESelectTemplateModalActions {
  OpenModal = 'OPEN_SELECT_TEMPLATE_MODAL',
  CloseModal = 'CLOSE_SELECT_TEMPLATE_MODAL',
  LoadSelectTemplateModalTemplates = 'LOAD_SELECT_TEMPLATE_MODAL_TEMPLATES',
  SetSelectTemplateModalTemplates = 'SET_SELECT_TEMPLATE_MODAL_TEMPLATES',
}

export type TOpenModalPayload = { templatesIdsFilter?: number[], ancestorTaskId?: number };
export type TOpenSelectTemplateModal = ITypedReduxAction<ESelectTemplateModalActions.OpenModal, TOpenModalPayload>;
export const openSelectTemplateModal: (payload?: TOpenModalPayload) => TOpenSelectTemplateModal =
  actionGenerator<ESelectTemplateModalActions.OpenModal, TOpenModalPayload>(ESelectTemplateModalActions.OpenModal);

export type TCloseSelectTemplateModal = ITypedReduxAction<ESelectTemplateModalActions.CloseModal, void>;
export const closeSelectTemplateModal: (payload?: void) => TCloseSelectTemplateModal =
  actionGenerator<ESelectTemplateModalActions.CloseModal, void>(ESelectTemplateModalActions.CloseModal);

export type TLoadSelectTemplateModalTemplates =
  ITypedReduxAction<ESelectTemplateModalActions.LoadSelectTemplateModalTemplates, void>;

export const loadSelectTemplateModalTemplates: (payload?: void) => TLoadSelectTemplateModalTemplates =
  actionGenerator<ESelectTemplateModalActions.LoadSelectTemplateModalTemplates, void>
  (ESelectTemplateModalActions.LoadSelectTemplateModalTemplates);

export type TSetSelectTemplateModalTemplates =
  ITypedReduxAction<ESelectTemplateModalActions.SetSelectTemplateModalTemplates, ITemplateListItem[]>;

export const setSelectTemplateModalTemplates: (payload: ITemplateListItem[]) => TSetSelectTemplateModalTemplates =
  actionGenerator<ESelectTemplateModalActions.SetSelectTemplateModalTemplates, ITemplateListItem[]>
  (ESelectTemplateModalActions.SetSelectTemplateModalTemplates);

export type TSelectTemplateModalActions =
  | TOpenSelectTemplateModal
  | TCloseSelectTemplateModal
  | TLoadSelectTemplateModalTemplates
  | TSetSelectTemplateModalTemplates;
