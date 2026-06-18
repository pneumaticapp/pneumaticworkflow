import { EWorkflowLogEvent } from '../../../../types/workflow';
import { isWorkflowEndedEventType } from '../isWorkflowEndedEventType';

describe('isWorkflowEndedEventType', () => {
  it('returns true for workflow completion events', () => {
    expect(isWorkflowEndedEventType(EWorkflowLogEvent.WorkflowComplete)).toBe(true);
    expect(isWorkflowEndedEventType(EWorkflowLogEvent.WorkflowFinished)).toBe(true);
    expect(isWorkflowEndedEventType(EWorkflowLogEvent.WorkflowEndedOnCondition)).toBe(true);
  });

  it('returns false for other workflow log events', () => {
    expect(isWorkflowEndedEventType(EWorkflowLogEvent.TaskComment)).toBe(false);
    expect(isWorkflowEndedEventType(EWorkflowLogEvent.TaskComplete)).toBe(false);
  });
});
