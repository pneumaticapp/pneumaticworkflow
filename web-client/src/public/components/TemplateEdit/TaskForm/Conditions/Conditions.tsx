import * as React from 'react';
import produce from 'immer';
import { useIntl } from 'react-intl';
import * as classnames from 'classnames';

import { isArrayWithItems } from '../../../../utils/helpers';
import { DropdownList } from '../../../UI/DropdownList';
import { TTaskVariable } from '../../types';
import { TUserListItem } from '../../../../types/user';
import { TrashIcon } from '../../../icons';
import { usePrevious } from '../../../../hooks/usePrevious';
import { SelectMenu } from '../../../UI';

import { ICondition } from '.';
import { ConditionValueField } from './ConditionValueField';
import { EConditionAction, EConditionLogicOperations, EConditionOperators, TConditionRule } from './types';
import { getEmptyConditions } from './utils/getEmptyConditions';
import { getEmptyRule } from './utils/getEmptyRule';
import { getDropdownOperators, IDropdownOperator } from './utils/getDropdownOperators';
import { setRulesApiNamesAndIds } from './utils/setRulesApiNames';

import styles from './Conditions.css';

export interface IConditionsProps {
  conditions: ICondition[];
  variables: TTaskVariable[];
  users: TUserListItem[];
  isSubscribed: boolean;
  onEdit(value: ICondition[]): void;
}

export interface IDropdownVariable extends TTaskVariable {
  label: string;
  richLabel: any;
}

export const OPERATORS_WITHOUT_VALUE = [EConditionOperators.Exist, EConditionOperators.NotExist];

export function Conditions({ conditions, variables, users, isSubscribed, onEdit }: IConditionsProps) {
  const { messages, formatMessage } = useIntl();

  const prevVariables = usePrevious(variables);

  React.useEffect(() => {
    const deletedFields = prevVariables
      ?.filter((prevVariable) => !variables.some(({ apiName }) => apiName === prevVariable.apiName))
      .map((variable) => variable.apiName);

    if (!deletedFields?.length) {
      return undefined;
    }

    const newConditions = conditions.map((condition) => {
      const notDeletedRules = condition.rules.filter((rule) => !rule.field || !deletedFields.includes(rule.field));

      return { ...condition, rules: notDeletedRules };
    });

    onEdit(newConditions);

    return undefined;
  }, [variables]);

  const dropdownVariables: IDropdownVariable[] = variables.map((variable) => ({
    ...variable,
    label: `${variable.subtitle}: ${variable.title}`,
    richLabel: (
      <div className={styles['rich-label']}>
        {variable.richSubtitle}: {variable.title}
      </div>
    ),
  }));

  const handleAddNewRule = () => {
    if (!isArrayWithItems(conditions)) {
      const newConditions = getEmptyConditions(isSubscribed);
      onEdit(newConditions);

      return;
    }

    const { rules } = conditions[0];
    const newConditions = [
      {
        ...conditions[0],
        rules: setRulesApiNamesAndIds([...rules, getEmptyRule()]),
      },
    ];

    onEdit(newConditions);
  };

  const handleChangeCondition = (conditionIndex: number) => (changedFields: Partial<ICondition>) => {
    const newConditions = produce(conditions, (draftConditions) => {
      const initialCondition = draftConditions[conditionIndex] as ICondition;
      const newCondition = { ...initialCondition, ...changedFields } as ICondition;
      draftConditions[conditionIndex] = newCondition;
    });

    onEdit(newConditions);
  };

  const handleChangeRule = (conditionIndex: number, ruleIndex: number) => (changedFields: Partial<TConditionRule>) => {
    const newConditions = produce(conditions, (draftConditions) => {
      const initialRule = draftConditions[conditionIndex].rules[ruleIndex] as TConditionRule;
      const newRule = { ...initialRule, ...changedFields } as TConditionRule;
      draftConditions[conditionIndex].rules[ruleIndex] = newRule;

      const { rules } = draftConditions[conditionIndex];
      draftConditions[conditionIndex].rules = setRulesApiNamesAndIds(rules);
    });

    onEdit(newConditions);
  };

  const handleRemoveRule = (conditionIndex: number) => (ruleIndex: number) => () => {
    const newConditions = produce(conditions, (draftConditions) => {
      const newRules = draftConditions[conditionIndex].rules.filter((item, index) => index !== ruleIndex);
      draftConditions[conditionIndex].rules = newRules;
    });

    onEdit(newConditions);
  };

  const renderConditions = () => {
    if (!isArrayWithItems(conditions)) {
      return null;
    }

    return <div className={styles['conditions']}>{conditions.map(rendeCondition)}</div>;
  };

  const rendeCondition = (condition: ICondition, conditionIndex: number) => {
    const { rules } = condition;

    if (!isArrayWithItems(rules)) {
      return null;
    }

    return (
      <div key={condition.apiName} className={styles['condition']}>
        <div className={styles['condition__rules']}>
          {rules.map((rule, ruleIndex) => {
            const changeCurrentRule = handleChangeRule(conditionIndex, ruleIndex);
            const selectedVariable = dropdownVariables.find((variable) => variable.apiName === rule.field) || null;
            const dropdownOperators = selectedVariable
              ? getDropdownOperators(selectedVariable.type, messages as Record<string, string>)
              : [];
            const selectedOperator = dropdownOperators?.find(({ operator }) => operator === rule.operator) || null;

            return (
              <div key={`${rule.ruleApiName}-${rule.predicateApiName}`} className={styles['condition-rule']}>
                {ruleIndex !== 0 && (
                  <div className={styles['condition-rule__logic-operation']}>
                    {rule.logicOperation && (
                      <SelectMenu
                        isDisabled={!isSubscribed}
                        hideSelectedOption
                        activeValue={rule.logicOperation}
                        containerClassName={styles['select']}
                        toggleClassName={styles['select-toggle']}
                        values={Object.values(EConditionLogicOperations)}
                        onChange={(logicOperation) => changeCurrentRule({ logicOperation })}
                      />
                    )}
                  </div>
                )}
                <div className={styles['condition-rule__settings']}>
                  <div
                    className={classnames(
                      styles['condition-rule__settings-inner'],
                      !isSubscribed && styles['condition-rule__settings_disabled'],
                    )}
                  >
                    <div className={classnames(styles['condition-rule__setting'], styles['condition-rule__field'])}>
                      <DropdownList
                        isDisabled={!isSubscribed}
                        placeholder={formatMessage({ id: 'templates.conditions.field-placeholder' })}
                        isSearchable={false}
                        value={selectedVariable}
                        getOptionLabel={(option: IDropdownVariable) => option.richLabel}
                        onChange={(option: IDropdownVariable) => {
                          if (option.apiName === rule.field) return;

                          changeCurrentRule({
                            fieldType: option.type,
                            field: option.apiName,
                            value: undefined,
                            operator: undefined,
                          });
                        }}
                        isClearable={false}
                        options={dropdownVariables}
                      />
                    </div>

                    <div className={classnames(styles['condition-rule__setting'], styles['condition-rule__operator'])}>
                      <DropdownList
                        isDisabled={!isSubscribed}
                        placeholder={formatMessage({ id: 'templates.conditions.operator-placeholder' })}
                        isSearchable={false}
                        value={selectedOperator}
                        onChange={(option: IDropdownOperator) => {
                          if (option.operator === rule.operator) {
                            return;
                          }

                          const shouldClearValue = OPERATORS_WITHOUT_VALUE.includes(option.operator);

                          changeCurrentRule({
                            operator: option.operator,
                            ...(shouldClearValue && { value: undefined }),
                          });
                        }}
                        isClearable={false}
                        options={dropdownOperators}
                      />
                    </div>
                    <ConditionValueField
                      isDisabled={!isSubscribed}
                      variable={selectedVariable}
                      operator={selectedOperator?.operator}
                      rule={rule}
                      users={users}
                      changeRuleValue={(value) => changeCurrentRule({ value })}
                    />

                    <button
                      type="button"
                      aria-label={formatMessage({ id: 'templates.conditions.remove-condition-rule' })}
                      onClick={handleRemoveRule(conditionIndex)(ruleIndex)}
                      className={styles['condition-rule__remove']}
                    >
                      <TrashIcon />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <SelectMenu
          isDisabled={!isSubscribed}
          hideSelectedOption
          activeValue={condition.action}
          containerClassName={styles['select']}
          toggleClassName={styles['select-toggle']}
          values={Object.values(EConditionAction)}
          onChange={(action) => handleChangeCondition(conditionIndex)({ action })}
        />
      </div>
    );
  };

  return (
    <div className={styles['container']}>
      {renderConditions()}

      {isSubscribed && (
        <button type="button" onClick={handleAddNewRule} className={styles['condition__add-rule']}>
          {formatMessage({ id: 'templates.conditions.add-new-rule' })}
        </button>
      )}
    </div>
  );
}
