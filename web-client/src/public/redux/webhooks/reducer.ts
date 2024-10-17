/* eslint-disable */
/* prettier-ignore */

import produce from 'immer';
import { TWebhooksActions, EWebhooksActions } from './actions';
import { EWebhooksSubscriberStatus, EWebhooksTypeEvent } from '../../types/webhooks';
import { IWebhookStore } from '../../types/redux';

const initialWebhooks: IWebhookStore = {
  [EWebhooksTypeEvent.workflowStarted]: {
    status: EWebhooksSubscriberStatus.Unknown,
    url: null,
  },
  [EWebhooksTypeEvent.workflowCompleted]: {
    status: EWebhooksSubscriberStatus.Unknown,
    url: null,
  },
  [EWebhooksTypeEvent.taskCompleted]: {
    status: EWebhooksSubscriberStatus.Unknown,
    url: null,
  },
  [EWebhooksTypeEvent.taskReturned]: {
    status: EWebhooksSubscriberStatus.Unknown,
    url: null,
  },
};

export const reducer = (state = initialWebhooks, action: TWebhooksActions): IWebhookStore => {
  switch (action.type) {
    case EWebhooksActions.SetWebhooksUrl:
      return produce(state, draftState => {
        draftState[action.payload.event].url = action.payload.url;
      });

    case EWebhooksActions.SetWebhooksStatus:
      return produce(state, draftState => {
        draftState[action.payload.event].status = action.payload.status;
      });

  default: return state;
  }
};
