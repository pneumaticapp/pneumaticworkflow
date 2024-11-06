import { IDueDate } from '../../types/template';
import { createDueDateApiName } from '../createId';

export function createEmptyDueDate(): IDueDate {
  return {
    apiName: createDueDateApiName(),
    duration: null,
    durationMonths: null,
    rulePreposition: 'after',
    ruleTarget: null,
    sourceId: null,
  };
}
