import { ITemplateTaskClient } from '../../../../types/template';
import { EConditionAction, ICondition, TConditionRule } from '../../TaskForm/Conditions';
import { EStartingType } from '../../TaskForm/Conditions/utils/getDropdownOperators';
import { getKickoffConditions } from '../../TaskForm/Conditions/utils/getKickoffConditions';
import { getStartTaskConditions } from '../../TaskForm/Conditions/utils/getStartTaskConditions';
import { getBaseStartRule } from '../../TaskForm/Conditions/utils/getStartTaskRule';
import { IGraphNewTaskDraft, TGraphAddTaskIntent } from '../types';
import { KICKOFF_NODE_ID } from './graphConstants';

export interface IInsertGraphTaskResult {
  tasks: ITemplateTaskClient[];
  createdApiName: string | null;
}

function getContinueConditions(afterId: string): ICondition[] {
  if (afterId === KICKOFF_NODE_ID) {
    return getKickoffConditions();
  }

  return getStartTaskConditions(afterId);
}

function isStartRuleFrom(rule: TConditionRule, fromId: string): boolean {
  if (fromId === KICKOFF_NODE_ID) {
    return rule.fieldType === EStartingType.Kickoff;
  }

  return rule.field === fromId;
}

function replaceStartAfterSource(
  task: ITemplateTaskClient,
  fromId: string,
  toId: string,
): ITemplateTaskClient {
  const startConditions = task.conditions.filter(
    (condition) => condition.action === EConditionAction.StartTask,
  );
  const otherConditions = task.conditions.filter(
    (condition) => condition.action !== EConditionAction.StartTask,
  );

  if (startConditions.length === 0) {
    return {
      ...task,
      conditions: [...getStartTaskConditions(toId), ...otherConditions],
    };
  }

  let replaced = false;
  const nextStart = startConditions.map((condition) => ({
    ...condition,
    rules: condition.rules.map((rule) => {
      if (!isStartRuleFrom(rule, fromId)) {
        return rule;
      }

      replaced = true;

      return getBaseStartRule(toId);
    }),
  }));

  const firstStart = nextStart[0];
  if (!replaced && firstStart) {
    return {
      ...task,
      conditions: [
        {
          ...firstStart,
          rules: [...firstStart.rules, getBaseStartRule(toId)],
        },
        ...nextStart.slice(1),
        ...otherConditions,
      ],
    };
  }

  return {
    ...task,
    conditions: [...nextStart, ...otherConditions],
  };
}

function withNumbers(tasks: ITemplateTaskClient[]): ITemplateTaskClient[] {
  return tasks.map((task, index) => ({ ...task, number: index + 1 }));
}

export function insertGraphTask(
  tasks: ITemplateTaskClient[],
  intent: TGraphAddTaskIntent,
  createTask: (draft: IGraphNewTaskDraft) => ITemplateTaskClient,
): IInsertGraphTaskResult {
  const newTaskNumber = tasks.length + 1;
  const created = createTask({
    name: `New Step ${newTaskNumber}`,
    number: newTaskNumber,
    conditions: getContinueConditions(intent.afterId),
  });

  if (intent.kind === 'continue') {
    return {
      tasks: withNumbers([...tasks, created]),
      createdApiName: created.apiName,
    };
  }

  const sorted = [...tasks].sort((a, b) => a.number - b.number);
  const beforeIndex = sorted.findIndex((task) => task.apiName === intent.beforeId);

  if (beforeIndex < 0) {
    return { tasks, createdApiName: null };
  }

  const nextTasks = [
    ...sorted.slice(0, beforeIndex),
    created,
    ...sorted.slice(beforeIndex),
  ].map((task) => {
    if (task.apiName !== intent.beforeId) {
      return task;
    }

    return replaceStartAfterSource(task, intent.afterId, created.apiName);
  });

  return {
    tasks: withNumbers(nextTasks),
    createdApiName: created.apiName,
  };
}
