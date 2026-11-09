import type { IntlShape } from 'react-intl';
import {
  EExtraFieldType,
  ITemplateKickoffClient,
  ITemplateTaskClient,
  TDueDateRuleTarget,
} from '../../../../../types/template';
import { TDropdownOptionBase } from '../../../../UI';
import { getPreviousTasks } from '../../utils/getPreviousTasks';
import { getTaskVariables } from '../../utils/getTaskVariables';

export type TRuleTargetOption = TDropdownOptionBase & {
  ruleTarget: TDueDateRuleTarget;
  sourceId: string | null;
};

export function getRuleTargetOptions(
  currentTask: ITemplateTaskClient,
  tasks: ITemplateTaskClient[],
  kickoff: ITemplateKickoffClient,
  formatMessage?: IntlShape['formatMessage'],
): readonly [TRuleTargetOption[], TRuleTargetOption[], TRuleTargetOption[]] {
  const prevTasks = getPreviousTasks(currentTask, tasks);
  const prevDateVariables = getTaskVariables(kickoff, tasks, currentTask).filter(
    (variable) => variable.type === EExtraFieldType.Date,
  );

  const systemRules = [
    {
      label: formatMessage ? formatMessage({ id: 'due-date.workflow-started' }) : 'Workflow started',
      sourceId: null,
      ruleTarget: 'workflow started',
    },
    {
      label: formatMessage ? formatMessage({ id: 'due-date.task-started' }) : 'This task started',
      sourceId: currentTask.apiName,
      ruleTarget: 'task started',
    },
  ].filter(Boolean) as TRuleTargetOption[];

  const dateFieldsRules: TRuleTargetOption[] = prevDateVariables.map((dateVariable) => {
    return {
      label: dateVariable.title,
      sourceId: dateVariable.apiName,
      ruleTarget: 'field',
    };
  });

  const tasksRules: TRuleTargetOption[] = prevTasks.map((task) => {
    return {
      label: task.name,
      sourceId: task.apiName,
      ruleTarget: 'task completed',
    };
  });

  return [systemRules, dateFieldsRules, tasksRules];
}
