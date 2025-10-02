import React from 'react';
import produce from 'immer';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { isArrayWithItems } from '../../../../utils/helpers';
import { EStartingType, getDropdownOperators } from './utils/getDropdownOperators';
import { setRulesApiNamesAndIds } from './utils/setRulesApiNames';
import { handleAddNewRule, handleAddNewCondition, CONDITION_DISABLED_OPERATOR, getDropdownSteps } from './utils/shared';

import { getSubscriptionPlan } from '../../../../redux/selectors/user';
import { EConditionAction, TConditionRule } from './types';
import { ESubscriptionPlan } from '../../../../types/account';
import { ICondition, IConditionsProps, IDropdownVariable, Predicate, RichLabel } from '.';

import styles from './Conditions.css';
import stylesTaskForm from '../TaskForm.css';

export function StartAfterCondition({ startingOrder, conditions, variables, isSubscribed, onEdit }: IConditionsProps) {
  const { messages, formatMessage } = useIntl();
  const billingPlan = useSelector(getSubscriptionPlan);
  const isFreePlan = billingPlan === ESubscriptionPlan.Free;
  const accessConditions = isSubscribed || isFreePlan;
  const checkIfConditions = conditions.filter((condition) => condition.action !== EConditionAction.StartTask);
  const startTaskCondition = conditions.find((condition) => condition.action === EConditionAction.StartTask);

  const handleChangeRule = (ruleIndex: number) => (changedFields: Partial<TConditionRule>) => {
    if (!startTaskCondition) return;

    const newStartTaskCondition = produce(startTaskCondition, (draftCondition) => {
      const initialRule = draftCondition.rules[ruleIndex] as TConditionRule;
      const newRule = { ...initialRule, ...changedFields } as TConditionRule;
      draftCondition.rules[ruleIndex] = newRule;

      const { rules } = draftCondition;
      draftCondition.rules = setRulesApiNamesAndIds(rules);
    });

    onEdit([newStartTaskCondition, ...checkIfConditions]);
  };

  const handleRemoveRule = () => (ruleIndex: number) => () => {
    if (!startTaskCondition) return;

    const newStartTaskCondition = produce(startTaskCondition, (draftCondition) => {
      draftCondition.rules = draftCondition.rules.filter((_, index) => index !== ruleIndex);
    });

    onEdit([newStartTaskCondition, ...checkIfConditions]);
  };

  const renderCondition = (condition: ICondition) => {
    const { rules } = condition;

    if (!isArrayWithItems(rules) || condition.action !== EConditionAction.StartTask) return null;

    return (
      <div key={condition.apiName} className={styles['condition']}>
        <div className={styles['condition__rules']}>
          {rules.map((rule, ruleIndex) => {
            const changeCurrentRule = handleChangeRule(ruleIndex);

            const dropdownSteps: IDropdownVariable[] = getDropdownSteps({ startingOrder, variables, rule });

            const selectedStartingOrder =
              dropdownSteps.find((item) => rule.fieldType === EStartingType.Kickoff || item.apiName === rule.field) ||
              null;

            const selected = selectedStartingOrder;

            const displayedVariable = selectedStartingOrder && {
              ...selectedStartingOrder,
              richLabel: <RichLabel variable={selectedStartingOrder} variables={variables} isFromStartingOrder />,
            };

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
                handleRemoveRule={handleRemoveRule}
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
            {formatMessage({ id: 'templates.starts-when.add-another-rule' })}
          </button>
        )}
      </div>
    );
  };

  const renderConditions = () => {
    if (!startTaskCondition)
      return (
        accessConditions && (
          <button
            type="button"
            onClick={() => handleAddNewCondition({ order: 1, conditions, accessConditions, onEdit, startTask: true })}
            className={classnames(stylesTaskForm['taskform__add-rule'], stylesTaskForm['content-mt12'])}
            style={{ height: '2rem' }}
          >
            {formatMessage({ id: 'templates.conditions.add-a-rule' })}
          </button>
        )
      );
    if (!isArrayWithItems(startTaskCondition?.rules))
      return (
        accessConditions && (
          <button
            type="button"
            onClick={() =>
              handleAddNewRule({
                conditionApiName: startTaskCondition?.apiName || '',
                conditions,
                accessConditions,
                onEdit,
              })
            }
            className={classnames(stylesTaskForm['taskform__add-rule'], stylesTaskForm['content-mt12'])}
            style={{ height: '2rem' }}
          >
            {formatMessage({ id: 'templates.conditions.add-a-rule' })}
          </button>
        )
      );

    return (
      <div className={classnames(styles['conditions'], stylesTaskForm['content-mt16'])}>
        {conditions.map(renderCondition)}
      </div>
    );
  };

  return <div className={classnames(styles['container'], stylesTaskForm['taskform__box'])}>{renderConditions()}</div>;
}
