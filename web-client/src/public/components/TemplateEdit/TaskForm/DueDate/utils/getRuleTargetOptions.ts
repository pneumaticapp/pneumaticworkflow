import { EExtraFieldType, IKickoff, ITemplateTask, TDueDateRuleTarget } from '../../../../../types/template';
import { TDropdownOptionBase } from '../../../../UI';
import { getPreviousTask } from '../../utils/getPreviousTask';
import { getPreviousTasks } from '../../utils/getPreviousTasks';
import { getTaskVariables } from '../../utils/getTaskVariables';

export type TRuleTargetOption = TDropdownOptionBase & {
  ruleTarget: TDueDateRuleTarget;
  sourceId: string | null;
};

export function getRuleTargetOptions(
  currentTask: ITemplateTask,
  tasks: ITemplateTask[],
  kickoff: IKickoff,
): readonly [TRuleTargetOption[], TRuleTargetOption[], TRuleTargetOption[]] {
  const prevTask = getPreviousTask(currentTask, tasks);
  const prevTasks = getPreviousTasks(currentTask, tasks);
  const prevDateVariables = getTaskVariables(kickoff, tasks, currentTask).filter(
    (variable) => variable.type === EExtraFieldType.Date,
  );

  const systemRules = [
    {
      label: 'Workflow started',
      sourceId: null,
      ruleTarget: 'workflow started',
    },
    {
      label: 'This task started',
      sourceId: currentTask.apiName,
      ruleTarget: 'task started',
    },
    prevTask && {
      label: 'Previous task completed',
      sourceId: prevTask.apiName,
      ruleTarget: 'task completed'
    },
  ].filter(Boolean) as TRuleTargetOption[];

  const dateFieldsRules: TRuleTargetOption[] = prevDateVariables.map(dateVariable => {
    return {
      label: dateVariable.title,
      sourceId: dateVariable.apiName,
      ruleTarget: 'field',
    }
  });

  const tasksRules: TRuleTargetOption[] = prevTasks.map(task => {
    return {
      label: task.name,
      sourceId: task.apiName,
      ruleTarget: 'task completed',
    }
  });

  return [
    systemRules,
    dateFieldsRules,
    tasksRules,
  ];
}
