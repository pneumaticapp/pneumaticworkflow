import * as React from 'react';
import { RouteComponentProps } from 'react-router-dom';

import { ETaskCardViewMode, TaskCardContainer } from '../TaskCard';
import { TLoadCurrentTaskPayload } from '../../redux/actions';
import { useDocumentTitle } from '../../hooks/useDocumentTitle';
import { ITask } from '../../types/tasks';

import styles from './TaskDetail.css';

export interface ITaskDetailPathParams {
  id: string;
}

export interface ITaskDetailProps extends RouteComponentProps {
  loadCurrentTask(payload: TLoadCurrentTaskPayload): void;
  task: ITask | null;
  viewMode?: ETaskCardViewMode;
}

export function TaskDetail({ task, match, viewMode = ETaskCardViewMode.Single, loadCurrentTask }: ITaskDetailProps) {
  const { useEffect } = React;

  useDocumentTitle('TasksDetail', task ? `${task.workflow.name} — ${task.name}` : undefined);

  useEffect(() => {
    const { id: taskId } = match.params as ITaskDetailPathParams;
    const normalizedTaskId = Number(taskId);

    loadCurrentTask({ taskId: normalizedTaskId, viewMode });
  }, []);

  return (
    <div className={styles['container']}>
      <TaskCardContainer viewMode={viewMode} />
    </div>
  );
}
