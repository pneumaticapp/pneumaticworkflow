import {
  IDueDate,
  IDueDateAPI,
  ITemplateTaskResponse,
  TDueDateRulePreposition,
  TDueDateRuleTarget,
} from '../../types/template';
import { createDueDateApiName } from '../createId';
import { createEmptyTaskDueDate } from './createEmptyTaskDueDate';

export const normalizeDueDateForFrontend = ({
  dueIn,
  apiName: taskApiName,
  rawDueDate,
}: ITemplateTaskResponse): IDueDate => {
  if (dueIn && taskApiName) {
    return {
      apiName: createDueDateApiName(),
      duration: dueIn,
      durationMonths: 0,
      rulePreposition: 'after',
      ruleTarget: 'task started',
      sourceId: taskApiName,
    };
  }

  if (rawDueDate) {
    const { apiName, duration, durationMonths, sourceId, rule } = rawDueDate;
    const [rulePreposition, ruleTarget] = convertRule(rule);

    return {
      apiName,
      duration,
      durationMonths: durationMonths || 0,
      sourceId,
      rulePreposition,
      ruleTarget,
    };
  }

  return createEmptyTaskDueDate(taskApiName);
};

const convertRule = (rule: IDueDateAPI['rule']): readonly [TDueDateRulePreposition, TDueDateRuleTarget | null] => {
  if (!rule) {
    return ['after', null];
  }

  const rulePrepositionOptions: TDueDateRulePreposition[] = ['after', 'before'];
  const rulePreposition = rulePrepositionOptions.find((r) => rule.includes(r)) || 'after';

  const ruleTargetOptions: TDueDateRuleTarget[] = ['field', 'task completed', 'task started', 'workflow started'];
  const ruleTarget = ruleTargetOptions.find((r) => rule.includes(r)) || 'task completed';

  return [rulePreposition, ruleTarget];
};
