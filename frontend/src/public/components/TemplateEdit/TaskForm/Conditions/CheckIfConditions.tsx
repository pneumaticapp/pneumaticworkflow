/* eslint-disable indent */
import React, { useEffect } from 'react';
import produce from 'immer';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { isArrayWithItems } from '../../../../utils/helpers';
import { EStartingType, getDropdownOperators } from './utils/getDropdownOperators';
import { setRulesApiNamesAndIds } from './utils/setRulesApiNames';
import {
  handleAddNewCondition,
  handleAddNewRule,
  CONDITION_DISABLED_OPERATOR,
  getDeletedFields,
  getDropdownSteps,
  removeEmptyRules,
} from './utils/shared';

import { TTaskVariable } from '../../types';
import { TUserListItem } from '../../../../types/user';
import { ESubscriptionPlan } from '../../../../types/account';

import { getSubscriptionPlan } from '../../../../redux/selectors/user';
import { usePrevious } from '../../../../hooks/usePrevious';
import { EConditionAction, TConditionRule } from './types';
import { SelectMenu, Tooltip } from '../../../UI';
import { ICondition, Predicate, RichLabel } from '.';

import styles from './Conditions.css';
import stylesTaskForm from '../TaskForm.css';

export interface IConditionsProps {
  conditions: ICondition[];
  startingOrder: TTaskVariable[];
  variables: TTaskVariable[];
  users: TUserListItem[];
  isSubscribed: boolean;
  onEdit(value: ICondition[]): void;
}

export interface IDropdownVariable extends TTaskVariable {
  label: string;
  richLabel: any;
}

const CHECK_IF_VALUES = [EConditionAction.SkipTask, EConditionAction.EndProcess];
const CHECK_IF_CONDITIONS_ORDER = 2;

export function CheckIfConditions({
  startingOrder,
  conditions,
  variables,
  users,
  isSubscribed,
  onEdit,
}: IConditionsProps) {
  const { messages, formatMessage } = useIntl();
  const billingPlan = useSelector(getSubscriptionPlan);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;
  const startTaskCondition = conditions.find((condition) => condition.action === EConditionAction.StartTask);
  const checkIfConditions = conditions.filter((condition) => condition.action !== EConditionAction.StartTask);
  const prevVariables = usePrevious(variables);

  useEffect(() => {
    getDeletedFields({ variables, prevVariables, conditions, onEdit });
  }, [variables, prevVariables, conditions, onEdit]);

  const handleChangeCondition = (conditionIndex: number) => (changedFields: Partial<ICondition>) => {
    const newConditions = produce(checkIfConditions, (draftConditions) => {
      const initialCondition = draftConditions[conditionIndex] as ICondition;
      const newCondition = { ...initialCondition, ...changedFields } as ICondition;
      draftConditions[conditionIndex] = newCondition;
    });

    onEdit(startTaskCondition ? [startTaskCondition, ...newConditions] : newConditions);
  };

  const handleChangeRule = (conditionIndex: number, ruleIndex: number) => (changedFields: Partial<TConditionRule>) => {
    const newConditions = produce(checkIfConditions, (draftConditions) => {
      const initialRule = draftConditions[conditionIndex].rules[ruleIndex] as TConditionRule;
      const newRule = { ...initialRule, ...changedFields } as TConditionRule;
      draftConditions[conditionIndex].rules[ruleIndex] = newRule;

      const { rules } = draftConditions[conditionIndex];
      draftConditions[conditionIndex].rules = setRulesApiNamesAndIds(rules);
    });

    onEdit(startTaskCondition ? [startTaskCondition, ...newConditions] : newConditions);
  };

  const handleRemoveRule = (conditionIndex: number) => (ruleIndex: number) => () => {
    let newConditions = produce(checkIfConditions, (draftConditions) => {
      const newRules = draftConditions[conditionIndex].rules.filter((_, index) => index !== ruleIndex);
      draftConditions[conditionIndex].rules = newRules;
    });

    newConditions = removeEmptyRules(newConditions, CHECK_IF_CONDITIONS_ORDER);

    onEdit(startTaskCondition ? [startTaskCondition, ...newConditions] : newConditions);
  };

  const renderCondition = (condition: ICondition, conditionIndex: number) => {
    const { rules } = condition;

    if (!isArrayWithItems(rules)) return null;

    return (
      <div key={condition.apiName} className={styles['condition']}>
        <div className={styles['condition__rules']}>
          {rules.map((rule, ruleIndex) => {
            const changeCurrentRule = handleChangeRule(conditionIndex, ruleIndex);

            const dropdownSteps: IDropdownVariable[] = getDropdownSteps({ startingOrder, variables, rule });

            const dropdownVariables: IDropdownVariable[] = variables.map((variable) => {
              const isSelected = variable.apiName === rule.field;
              return {
                ...variable,
                label: `${variable.subtitle} ${variable.title}`,
                richLabel: <RichLabel variable={variable} variables={variables} isSelected={isSelected} />,
              };
            });

            const selectedStartingOrder =
              dropdownSteps.find((item) => rule.fieldType === EStartingType.Kickoff || item.apiName === rule.field) ||
              null;

            const selectedVariable = dropdownVariables.find((variable) => variable.apiName === rule.field) || null;
            const selected = selectedStartingOrder || selectedVariable;

            const displayedVariable =
              (selectedStartingOrder && {
                ...selectedStartingOrder,
                richLabel: <RichLabel variable={selectedStartingOrder} variables={variables} isFromStartingOrder />,
              }) ||
              (selectedVariable && {
                ...selectedVariable,
                richLabel: (
                  <Tooltip
                    interactive={false}
                    containerClassName={styles['condition__tooltop']}
                    contentClassName={styles['condition__tooltop-box']}
                    content={selectedVariable?.title}
                  >
                    <div className={styles['rich-label']}>
                      <div>{selectedVariable?.title}</div>
                    </div>
                  </Tooltip>
                ),
              });

            const dropdownOperators = selected
              ? getDropdownOperators(selected.type, messages as Record<string, string>)
              : [];
            const selectedOperator = dropdownOperators?.find(({ operator }) => operator === rule.operator) || null;

            const isDisabledOperator =
              (rule.fieldType && CONDITION_DISABLED_OPERATOR.includes(rule.fieldType)) || !accessConditions;

            const options = [
              {
                label: formatMessage({ id: 'templates.conditions.starting-order' }),
                options: dropdownSteps,
              },
              {
                label: formatMessage({ id: 'templates.conditions.variables-completed' }),
                options: dropdownVariables,
              },
            ];

            return (
              <Predicate
                key={rule.ruleApiName}
                rule={rule}
                ruleIndex={ruleIndex}
                accessConditions={accessConditions}
                changeCurrentRule={changeCurrentRule}
                displayedVariable={displayedVariable}
                isDisabledOperator={isDisabledOperator}
                selectedOperator={selectedOperator}
                dropdownOperators={dropdownOperators}
                selectedVariable={selectedVariable}
                users={users}
                handleRemoveRule={handleRemoveRule}
                conditionIndex={conditionIndex}
                isCheckIs
                options={options}
              />
            );
          })}
        </div>
        {accessConditions && (
          <button
            style={{ display: 'block', marginBottom: '0.8rem' }}
            type="button"
            onClick={() =>
              handleAddNewRule({ conditionApiName: condition.apiName, conditions, accessConditions, onEdit })
            }
            className={stylesTaskForm['taskform__add-rule']}
          >
            {formatMessage({ id: 'templates.conditions.add-another-rule' })}
          </button>
        )}
        <SelectMenu
          isDisabled={!accessConditions}
          hideSelectedOption
          activeValue={condition.action}
          containerClassName={styles['select']}
          toggleClassName={styles['select-toggle']}
          values={CHECK_IF_VALUES}
          onChange={(action: EConditionAction) => handleChangeCondition(conditionIndex)({ action })}
          isFromCheckIfConditions
        />
      </div>
    );
  };

  const renderConditions = () => {
    if (!isArrayWithItems(checkIfConditions))
      return (
        accessConditions && (
          <button
            type="button"
            onClick={() => handleAddNewCondition({ order: 2, conditions, accessConditions, onEdit })}
            className={classnames(stylesTaskForm['taskform__add-rule'], stylesTaskForm['content-mt12'])}
            style={{ height: '2rem' }}
          >
            {formatMessage({ id: 'templates.conditions.add-a-new-rule' })}
          </button>
        )
      );

    return (
      <div className={classnames(styles['conditions'], stylesTaskForm['content-mt16'])}>
        {checkIfConditions.map(renderCondition)}
      </div>
    );
  };

  return <div className={classnames(styles['container'], stylesTaskForm['taskform__box'])}>{renderConditions()}</div>;
}
