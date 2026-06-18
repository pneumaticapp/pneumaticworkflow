import { EWorkflowLogEvent } from '../../../types/workflow';

const WORKFLOW_ENDED_EVENT_TYPES = new Set<EWorkflowLogEvent>([
  EWorkflowLogEvent.WorkflowComplete,
  EWorkflowLogEvent.WorkflowFinished,
  EWorkflowLogEvent.WorkflowEndedOnCondition,
]);

export function isWorkflowEndedEventType(type: EWorkflowLogEvent): boolean {
  return WORKFLOW_ENDED_EVENT_TYPES.has(type);
}
