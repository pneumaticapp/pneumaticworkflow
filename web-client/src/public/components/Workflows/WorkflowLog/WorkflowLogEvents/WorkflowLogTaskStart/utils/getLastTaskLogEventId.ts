/* eslint-disable */
/* prettier-ignore */
import { EWorkflowsLogSorting, EWorkflowLogEvent, IWorkflowLogItem } from '../../../../../../types/workflow';
import { isArrayWithItems } from '../../../../../../utils/helpers';

export const getLastTaskLogEventId = (items: IWorkflowLogItem[], sorting: EWorkflowsLogSorting) => {
  const isProcessEnded = items.some(item => {
    return item.type === EWorkflowLogEvent.WorkflowFinished || item.type === EWorkflowLogEvent.WorkflowComplete;
  });

  if (isProcessEnded) {
    return null;
  }

  const startTaskEvents = items.filter(item => item.type === EWorkflowLogEvent.TaskStart);

  if (!isArrayWithItems(startTaskEvents)) {
    return null;
  }

  const lastTaskStartEvent = sorting === EWorkflowsLogSorting.New
    ? startTaskEvents.shift()
    : startTaskEvents.pop();

  return lastTaskStartEvent ? lastTaskStartEvent.id : null;
};
