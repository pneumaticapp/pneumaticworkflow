import {
  IDueDate,
  IDueDateAPI,
  ITemplateTaskResponse,
  TDueDateRulePreposition,
  TDueDateRuleTarget,
} from '../../types/template';
import { createDueDateApiName } from '../createId';
import { createEmptyDueDate } from './createEmptyDueDate';

export const normalizeDueDateForFrontend = (task: ITemplateTaskResponse): IDueDate => {
  if (task.dueIn && task.apiName) {
    return {
      apiName: createDueDateApiName(),
      duration: task.dueIn,
      durationMonths: 0,
      rulePreposition: 'after',
      ruleTarget: 'task started',
      sourceId: task.apiName,
    };
  }

  if (task.rawDueDate) {
    const [rulePreposition, ruleTarget] = convertRule(task.rawDueDate.rule);

    return {
      apiName: task.rawDueDate.apiName,
      duration: task.rawDueDate.duration,
      durationMonths: task.rawDueDate.durationMonths || null,
      sourceId: task.rawDueDate.sourceId,
      rulePreposition,
      ruleTarget,
    };
  }

  return createEmptyDueDate();
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
