import { START_DURATION } from '../../components/TemplateEdit/constants';
import { IDueDate, IDueDateAPI } from '../../types/template';

export const normalizeDueDateForBackend = ({
  rulePreposition,
  ruleTarget,
  apiName,
  duration,
  durationMonths,
  sourceId,
}: IDueDate): IDueDateAPI | null => {
  if (duration === null && durationMonths === null) {
    return null;
  }

  const rule = `${rulePreposition} ${ruleTarget}` as IDueDateAPI['rule'];

  return {
    apiName,
    duration: duration || START_DURATION,
    durationMonths: durationMonths || 0,
    sourceId,
    rule,
  };
};
