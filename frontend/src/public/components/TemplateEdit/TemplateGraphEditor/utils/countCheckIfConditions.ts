import { EConditionAction, ICondition } from '../../TaskForm/Conditions';
import { getConditionsCount } from '../../TaskItem/utlils/getConditionsCount';

const CHECK_IF_ACTIONS = new Set<EConditionAction>([
  EConditionAction.SkipTask,
  EConditionAction.EndProcess,
]);

export function isCheckIfCondition(condition: ICondition): boolean {
  return CHECK_IF_ACTIONS.has(condition.action);
}

export function countCheckIfConditions(conditions: ICondition[] | undefined): number {
  return getConditionsCount((conditions ?? []).filter(isCheckIfCondition));
}
