import { useCallback } from 'react';
import { useIntl } from 'react-intl';

import { ITemplateTaskClient } from '../types/template';
import { NotificationManager } from '../components/UI/Notifications';
import { START_DURATION } from '../components/TemplateEdit/constants';
import { updateTemplateTaskDelay } from '../components/TemplateEdit/utils/templateTaskList';

export interface ITemplateTaskDelayActions {
  addDelay(targetTask: ITemplateTaskClient): void;
  editDelay(targetTask: ITemplateTaskClient, delay: string): void;
  deleteDelay(targetTask: ITemplateTaskClient): void;
}

export function useTemplateTaskDelays(
  tasks: ITemplateTaskClient[],
  changeTasks: (tasks: ITemplateTaskClient[]) => void,
  toggleDelay: (taskUuid: string) => void,
): ITemplateTaskDelayActions {
  const { formatMessage } = useIntl();

  const editDelay = useCallback(
    (targetTask: ITemplateTaskClient, delay: string): void => {
      changeTasks(updateTemplateTaskDelay(tasks, targetTask, delay));
    },
    [changeTasks, tasks],
  );

  const deleteDelay = useCallback(
    (targetTask: ITemplateTaskClient): void => {
      if (targetTask.delay) editDelay(targetTask, '');
    },
    [editDelay],
  );

  const addDelay = useCallback(
    (targetTask: ITemplateTaskClient): void => {
      if (targetTask.delay) {
        NotificationManager.warning({
          message: formatMessage({ id: 'template.delay-task-has-delay-error' }),
        });
        return;
      }

      if (targetTask.number === 1) {
        NotificationManager.warning({
          message: formatMessage({ id: 'template.delay-first-task-delay-error' }),
        });
        return;
      }

      changeTasks(updateTemplateTaskDelay(tasks, targetTask, START_DURATION));
      toggleDelay(targetTask.uuid);
    },
    [changeTasks, formatMessage, tasks, toggleDelay],
  );

  return { addDelay, editDelay, deleteDelay };
}
