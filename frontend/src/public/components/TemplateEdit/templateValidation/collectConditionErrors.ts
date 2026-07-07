import { EExtraFieldType } from '../../../types/template';
import { numberRegex } from '../../../constants/defaultValues';
import { ETaskFormParts } from '../types';
import { EConditionAction, ICondition, TConditionRule } from '../TaskForm/Conditions/types';
import { getFilledConditions } from '../TaskForm/Conditions/utils/conditionsValidators';
import { OPERATORS_WITHOUT_VALUE } from '../TaskForm/Conditions/utils/shared';
import { TTemplateValidationError } from './types';

function getConditionFormPart(action: EConditionAction): ETaskFormParts {
  return action === EConditionAction.StartTask ? ETaskFormParts.StartsAfter : ETaskFormParts.CheckIf;
}

function collectRuleErrors(
  taskUuid: string,
  condition: ICondition,
  rule: TConditionRule,
): TTemplateValidationError[] {
  const formPart = getConditionFormPart(condition.action);
  const basePath = `tasks.${taskUuid}.conditions.${condition.apiName}.rules.${rule.ruleApiName}`;
  const scrollTarget = {
    area: 'task' as const,
    taskUuid,
    formPart,
    ruleApiName: rule.ruleApiName,
  };
  const errors: TTemplateValidationError[] = [];

  if ((!rule.field && rule.fieldType !== 'kickoff') || !rule.fieldType) {
    errors.push({
      path: `${basePath}.field`,
      messageId: 'template.validation.condition-field-required',
      scrollTarget,
    });
  }

  if (rule.fieldType !== 'kickoff' && rule.field && !rule.operator) {
    errors.push({
      path: `${basePath}.operator`,
      messageId: 'template.validation.condition-operator-required',
      scrollTarget,
    });
  }

  const ruleMustHaveValue = rule.operator && !OPERATORS_WITHOUT_VALUE.includes(rule.operator);
  if (ruleMustHaveValue && (rule.value === undefined || rule.value === null || rule.value === '')) {
    errors.push({
      path: `${basePath}.value`,
      messageId: 'template.validation.condition-value-required',
      scrollTarget,
    });
  }

  if (
    rule.fieldType === EExtraFieldType.Number
    && rule.value
    && !numberRegex.test(String(rule.value))
  ) {
    errors.push({
      path: `${basePath}.value`,
      messageId: 'validation.number-invalid-format',
      scrollTarget,
    });
  }

  return errors;
}

export function collectConditionErrors(taskUuid: string, conditions: ICondition[]): TTemplateValidationError[] {
  return getFilledConditions(conditions).flatMap((condition) =>
    condition.rules.flatMap((rule) => collectRuleErrors(taskUuid, condition, rule)),
  );
}
