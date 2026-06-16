import type { IWorkflowLogItem, IWorkflowLogTask } from '../../../types/workflow';
import { EWorkflowLogEvent } from '../../../types/workflow';
import type { RawPerformer } from '../../../types/template';
import { toISOStringFromTsp } from '../../../utils/dateTime';
import type { IRealtimeWsEnvelope, IWsEventCreatedTask, IWsTaskPerformer } from '../wsPayloads';



function mapPerformers(performers: IWsTaskPerformer[]): RawPerformer[] {
  return performers.map(({ sourceId, type }) => ({
    sourceId,
    type: type as RawPerformer['type'],
  }));
}

function logTaskFromEventCreatedTask(task: IWsEventCreatedTask): IWorkflowLogTask {
  return {
    id: task.id,
    name: task.name,
    number: task.number,
    description: task.description,
    output: [],
    performers: mapPerformers(task.performers),
    dueDate: toISOStringFromTsp(task.dueDateTsp),
    delay: null,
  };
}

export function mapWsEnvelopeToWorkflowLogItem(envelope: IRealtimeWsEnvelope): IWorkflowLogItem | null {
  if (envelope.type === 'event_created') {
    const { data } = envelope;
    return {
      id: data.id,
      workflowId: data.workflowId,
      created: toISOStringFromTsp(data.createdTsp),
      status: 'created',
      task: logTaskFromEventCreatedTask(data.task),
      text: null,
      type: data.type as EWorkflowLogEvent,
      userId: null,
      delay: null,
      targetUserId: null,
      targetGroupId: null,
      watched: [],
      reactions: {},
    };
  }

  if (envelope.type === 'event_updated') {
    const { data } = envelope;
    const reactions: IWorkflowLogItem['reactions'] = {};
    Object.keys(data.reactions).forEach((key) => {
      reactions[key] = (data.reactions[key] ?? []).map((uid) => ({ id: uid }));
    });

    const watched = data.watched.map((w) => ({
      date: toISOStringFromTsp(w.dateTsp),
      userId: { id: w.userId } as { id: number },
    }));

    const task: IWorkflowLogTask | null = data.task
      ? {
        id: data.task.id,
        name: data.task.name,
        number: data.task.number,
        description: '',
        output: [],
        performers: [],
        dueDate: null,
        delay: null,
      }
      : null;

    return {
      id: data.id,
      workflowId: data.workflowId,
      created: toISOStringFromTsp(data.createdTsp),
      status: data.status,
      task,
      text: data.text,
      type: data.type as EWorkflowLogEvent,
      userId: null,
      delay: null,
      targetUserId: null,
      targetGroupId: null,
      watched,
      reactions,
    };
  }

  return null;
}
