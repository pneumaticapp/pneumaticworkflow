import { IDueDate } from '../../types/template';
import { createDueDateApiName } from '../createId';

export function createEmptyTaskDueDate(sourceId: string | null = null): IDueDate {
  return {
    apiName: createDueDateApiName(),
    duration: null,
    durationMonths: null,
    rulePreposition: 'after',
    ruleTarget: 'task started',
    sourceId,
  };
}
