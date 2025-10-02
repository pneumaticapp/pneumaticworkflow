import React from 'react';
import { EExtraFieldType } from '../../../../../types/template';
import { isArrayWithItems } from '../../../../../utils/helpers';
import { TTaskVariable } from '../../../types';
import { RichLabel } from '../RichLabel';
import { EConditionAction, EConditionOperators, ICondition, TConditionRule } from '../types';
import { EStartingType } from './getDropdownOperators';
import { getEmptyConditions, getOneEmptyCondition } from './getEmptyConditions';
import { getEmptyRule } from './getEmptyRule';
import { setRulesApiNamesAndIds } from './setRulesApiNames';

interface IHandleAddNewConditionProps {
  order?: number;
  conditions: ICondition[];
  accessConditions: boolean;
  onEdit: (conditions: ICondition[]) => void;
  startTask?: boolean;
}
interface IHandleAddNewRuleProps {
  conditionApiName: string;
  conditions: ICondition[];
  accessConditions: boolean;
  onEdit: (conditions: ICondition[]) => void;
}
interface IGetDeletedFieldsProps {
  variables: TTaskVariable[];
  prevVariables?: TTaskVariable[];
  conditions: ICondition[];
  onEdit: (conditions: ICondition[]) => void;
}
interface IGetDropdownStepsProps {
  startingOrder: TTaskVariable[];
  variables: TTaskVariable[];
  rule: TConditionRule;
}

export const CONDITION_DISABLED_OPERATOR: (EStartingType | EExtraFieldType)[] = [
  EStartingType.Task,
  EStartingType.Kickoff,
];
export const OPERATORS_WITHOUT_VALUE = [
  EConditionOperators.Exist,
  EConditionOperators.NotExist,
  EConditionOperators.Completed,
];

export const handleAddNewCondition = ({
  order,
  conditions,
  accessConditions,
  onEdit,
  startTask,
}: IHandleAddNewConditionProps) => {
  const newCondition = getOneEmptyCondition(accessConditions, startTask ? 1 : order, startTask);
  return onEdit([...conditions, newCondition]);
};

export const handleAddNewRule = ({
  conditionApiName,
  conditions,
  accessConditions,
  onEdit,
}: IHandleAddNewRuleProps) => {
  if (!isArrayWithItems(conditions)) {
    const newConditions = getEmptyConditions(accessConditions);
    onEdit(newConditions);

    return;
  }

  const newConditions = conditions.map((condition) => {
    if (condition.apiName === conditionApiName) {
      return {
        ...condition,
        rules: setRulesApiNamesAndIds([...condition.rules, getEmptyRule()]),
      };
    }
    return condition;
  });
  onEdit(newConditions);
};

export const removeEmptyRules = (conditions: ICondition[], order?: number) => {
  return conditions
    ?.filter((condition) => condition.action === EConditionAction.StartTask || condition.rules.length !== 0)
    ?.map((condition, i) => ({
      ...condition,
      order: i + (order || 1),
    }));
};

export const removeDeletedTasks = (
  startingOrder: TTaskVariable[],
  conditions: ICondition[],
  onEdit: (conditions: ICondition[]) => void,
) => {
  const startingOrderApiNamesSet = new Set(startingOrder.map((task) => task.apiName));
  let hasChanges = false;

  let newConditions = conditions.map((condition) => {
    const filteredRules = condition.rules.filter(
      (rule) => rule.fieldType !== 'task' || (rule.field && startingOrderApiNamesSet.has(rule.field)),
    );
    if (!hasChanges && filteredRules.length !== condition.rules.length) {
      hasChanges = true;
    }
    return {
      ...condition,
      rules: filteredRules,
    };
  });

  if (hasChanges) {
    newConditions = removeEmptyRules(newConditions);
    onEdit(newConditions);
  }
};

export const getDeletedFields = ({ variables, prevVariables, conditions, onEdit }: IGetDeletedFieldsProps) => {
  const deletedFields = prevVariables
    ?.filter((prevVariable) => !variables.some(({ apiName }) => apiName === prevVariable.apiName))
    .map((variable) => variable.apiName);
  if (!deletedFields?.length) return undefined;
  let newConditions = conditions.map((condition) => {
    const notDeletedRules = condition.rules.filter((rule) => !rule.field || !deletedFields.includes(rule.field));

    return { ...condition, rules: notDeletedRules };
  });
  newConditions = removeEmptyRules(newConditions);
  onEdit(newConditions);

  return undefined;
};

export const getDropdownSteps = ({ startingOrder, variables, rule }: IGetDropdownStepsProps) => {
  return startingOrder.map((variable) => {
    const isSelected = variable.apiName === rule.field || (rule.field === null && variable.apiName === 'kick-off');
    return {
      ...variable,
      label: variable.title,
      richLabel: <RichLabel variable={variable} variables={variables} isSelected={isSelected} isFromStartingOrder />,
    };
  });
};
