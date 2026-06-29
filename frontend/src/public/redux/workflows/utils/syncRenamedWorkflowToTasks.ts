import { all, put } from 'redux-saga/effects';

import { setCurrentTask } from '../../actions';
import { patchTaskInList } from '../../tasks/slice';
import { ITask } from '../../../types/tasks';
import { IWorkflowTaskClient } from '../../../types/workflow';

export function getTaskWithRenamedWorkflow(
  task: ITask,
  workflowId: number,
  workflowName: string,
): ITask | null {
  const isMainWorkflow = workflowId === task.workflow.id;
  const isSubWorkflow = task.subWorkflows?.some((subWorkflow) => subWorkflow.id === workflowId);

  if (!isMainWorkflow && !isSubWorkflow) {
    return null;
  }

  return {
    ...task,
    ...(isMainWorkflow && {
      workflow: { ...task.workflow, name: workflowName },
    }),
    ...(isSubWorkflow && {
      subWorkflows: task.subWorkflows.map((subWorkflow) =>
        subWorkflow.id === workflowId ? { ...subWorkflow, name: workflowName } : subWorkflow,
      ),
    }),
  };
}

export function* syncRenamedWorkflowToTasks(
  task: ITask | null,
  workflowId: number,
  workflowName: string,
  workflowTasks: IWorkflowTaskClient[],
) {
  if (task) {
    const updatedTask = getTaskWithRenamedWorkflow(task, workflowId, workflowName);

    if (updatedTask) {
      yield put(setCurrentTask(updatedTask));
    }
  }

  yield all(
    workflowTasks.map((workflowTask) =>
      put(patchTaskInList({
        taskId: workflowTask.id,
        task: { workflowName },
      })),
    ),
  );
}
