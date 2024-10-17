import { EMPTY_DURATION } from '../../components/TemplateEdit/constants';
import { IDueDate, IDueDateAPI } from '../../types/template';

export const normalizeDueDateForBackend = (dueDate: IDueDate): IDueDateAPI | null => {
  if (!dueDate.ruleTarget) {
    return null;
  }

  const rule = `${dueDate.rulePreposition} ${dueDate.ruleTarget}` as IDueDateAPI['rule'];

  return {
    apiName: dueDate.apiName,
    duration: dueDate.duration || EMPTY_DURATION,
    durationMonths: dueDate.durationMonths || 0,
    sourceId: dueDate.sourceId,
    rule,
  };
};
