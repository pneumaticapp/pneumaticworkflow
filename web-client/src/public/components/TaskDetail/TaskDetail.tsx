import * as React from 'react';
import { RouteComponentProps } from 'react-router-dom';

import { ETaskCardViewMode, TaskCardContainer } from '../TaskCard';
import { TLoadCurrentTaskPayload } from '../../redux/actions';
import { PNEUMATIC_SUFFIX, TITLES } from '../../constants/titles';
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

  useEffect(() => {
    const pageTitle = task ? `${task.workflow.name} — ${task.name} ${PNEUMATIC_SUFFIX}` : TITLES.TasksDetail;

    document.title = pageTitle;
  }, [task]);

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
