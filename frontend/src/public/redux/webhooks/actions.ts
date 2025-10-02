/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-line-length
import { ITypedReduxAction } from '../../types/redux';
import { EWebhooksTypeEvent, IWebhook } from '../../types/webhooks';
import { actionGenerator } from '../../utils/redux';

export const enum EWebhooksActions {
  LoadWebhooks = 'LOAD_WEBHOOKS',
  SetWebhooksStatus = 'SET_WEBHOOKS_STATUS',
  SetWebhooksUrl = 'SET_WEBHOOKS_URL',
  AddWebhooks = 'ADD_WEBHOOKS',
  RemoveWebhooks = 'REMOVE_WEBHOOKS',
}

interface ISetWebhookStatusPayload extends Pick<IWebhook, 'status'> {
  event: EWebhooksTypeEvent;
}
interface ISetWebhookUrlPayload extends Pick<IWebhook, 'url'> {
  event: EWebhooksTypeEvent;
}

export type TLoadWebhooks = ITypedReduxAction<EWebhooksActions.LoadWebhooks, void>;
export const loadWebhooks: (payload?: void) => TLoadWebhooks =
  actionGenerator<EWebhooksActions.LoadWebhooks, void>(EWebhooksActions.LoadWebhooks);

export type TSetWebhooksUrl = ITypedReduxAction<EWebhooksActions.SetWebhooksUrl, ISetWebhookUrlPayload>;
export const setWebhooksUrl: (payload: ISetWebhookUrlPayload) => TSetWebhooksUrl =
  actionGenerator<EWebhooksActions.SetWebhooksUrl, ISetWebhookUrlPayload>(EWebhooksActions.SetWebhooksUrl);

export type TSetWebhooksStatus = ITypedReduxAction<EWebhooksActions.SetWebhooksStatus, ISetWebhookStatusPayload>;
export const setWebhooksStatus: (payload: ISetWebhookStatusPayload) => TSetWebhooksStatus =
  actionGenerator<EWebhooksActions.SetWebhooksStatus, ISetWebhookStatusPayload>(EWebhooksActions.SetWebhooksStatus);

export type TAddWebhook = ITypedReduxAction<EWebhooksActions.AddWebhooks, ISetWebhookUrlPayload>;
export const addWebhooks: (payload: ISetWebhookUrlPayload) => TAddWebhook =
  actionGenerator<EWebhooksActions.AddWebhooks, ISetWebhookUrlPayload>(EWebhooksActions.AddWebhooks);

export type TRemoveWebhook = ITypedReduxAction<EWebhooksActions.RemoveWebhooks, {event: EWebhooksTypeEvent}>;
export const removeWebhooks: (payload: {event: EWebhooksTypeEvent }) => TRemoveWebhook =
  actionGenerator<EWebhooksActions.RemoveWebhooks, {event: EWebhooksTypeEvent}>(EWebhooksActions.RemoveWebhooks);

export type TWebhooksActions =
  | TLoadWebhooks
  | TSetWebhooksUrl
  | TSetWebhooksStatus
  | TAddWebhook
  | TRemoveWebhook;
