import * as React from 'react';
import { IWorkflow } from './workflow';

export type TNotificationType = 'info' | 'success' | 'warning' | 'error';

export interface INotification {
  id: string;
  type: TNotificationType;
  title: React.ReactNode | null;
  message: React.ReactNode | null;
  timeOut: number;
  customClassName: string;
  priority?: boolean;
  onCancelClick?: Function;
  onClick?: Function;
  onSubmitClick?: Function;
}

export type TNotificationsListItemStatus = 'new' | 'read';

export type TNotificationsListItemCommon = {
  id: number;
  status: TNotificationsListItemStatus;
  datetime: string;
};

export type TNotificationsListItemOptional =
  | {
      type: 'reaction';
      author: number;
      text: string;
      workflow: Pick<IWorkflow, 'id' | 'name'>;
      task: {
        id: number;
        name: string;
      };
    }
  | {
      type: 'mention';
      author: number;
      text: string;
      workflow: Pick<IWorkflow, 'id' | 'name'>;
      task: {
        id: number;
        name: string;
      };
    }
  | {
      type: 'comment';
      author: number;
      text: string;
      workflow: Pick<IWorkflow, 'id' | 'name'>;
      task: {
        id: number;
        name: string;
      };
    }
  | {
      type: 'system';
      text: string;
    }
  | {
      type: 'urgent';
      text: string;
      task: {
        id: number;
        name: string;
      };
      author: number;
      workflow: {
        id: number;
        name: string;
      };
    }
  | {
      type: 'not_urgent';
      text: string;
      task: {
        id: number;
        name: string;
      };
      author: number;
      workflow: {
        id: number;
        name: string;
      };
    }
  | {
      type: 'overdue_task';
      workflow: {
        id: number;
        name: string;
      };
      task: {
        id: number;
        name: string;
      };
    }
  | {
      type: 'snooze_workflow';
      author: number;
      workflow: {
        id: number;
        name: string;
      };
      task: {
        id: number;
        name: string;
        delay: {
          estimatedEndDate: string;
          duration: string;
        } | null;
      };
    }
  | {
      type: 'resume_workflow';
      author: number;
      workflow: {
        id: number;
        name: string;
      };
      task: {
        id: number;
        name: string;
      };
    };

export type TNotificationsListItem = TNotificationsListItemCommon & TNotificationsListItemOptional;
