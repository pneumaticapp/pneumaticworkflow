import { produce } from 'immer';
import { EWebhooksActions } from './actions';
import type { TWebhooksActions } from './actions';
import { EWebhooksSubscriberStatus, EWebhooksTypeEvent } from '../../types/webhooks';
import type { TWebhookStore } from './types';

const initialWebhooks: TWebhookStore = {
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

export const reducer = (state = initialWebhooks, action: TWebhooksActions): TWebhookStore => {
  switch (action.type) {
    case EWebhooksActions.SetWebhooksUrl:
      return produce(state, (draftState) => {
        if (draftState[action.payload.event]) {
          draftState[action.payload.event].url = action.payload.url;
        }
      });

    case EWebhooksActions.SetWebhooksStatus:
      return produce(state, (draftState) => {
        if (draftState[action.payload.event]) {
          draftState[action.payload.event].status = action.payload.status;
        }
      });

    default:
      return state;
  }
};
