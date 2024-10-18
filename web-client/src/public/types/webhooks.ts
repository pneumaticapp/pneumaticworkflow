export interface IWebhook {
  status: EWebhooksSubscriberStatus;
  url: IWebhookUrl;
}

export type IWebhookUrl = string | null;

export enum EWebhooksTypeEvent {
  workflowStarted = 'workflow_started',
  workflowCompleted = 'workflow_completed',
  taskCompleted = 'task_completed_v2',
  taskReturned = 'task_returned',
}

export enum EWebhooksSubscriberStatus {
  Unknown = 'unknown',
  Loading = 'loading',
  Subscribed = 'subscribed',
  Subscribing = 'subscribing',
  Unsubscribing = 'unsubscribing',
  NotSubscribed = 'not-subscribed',
}
