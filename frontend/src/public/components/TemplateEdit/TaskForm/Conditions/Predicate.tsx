/* eslint-disable indent */
import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { DropdownList, SelectMenu } from '../../../UI';
import { IDropdownOperator } from './utils/getDropdownOperators';
import { CONDITION_DISABLED_OPERATOR, OPERATORS_WITHOUT_VALUE } from './utils/shared';
import { getFormattedDropdownOption } from './utils/getFormattedDropdownOption';
import { ConditionValueField } from './ConditionValueField';
import { TrashIcon } from '../../../icons';
import { EConditionLogicOperations, EConditionOperators, TConditionRule } from './types';
import { TUserListItem } from '../../../../types/user';
import { IDropdownVariable } from './CheckIfConditions';

import styles from './Conditions.css';
import stylesTaskForm from '../TaskForm.css';

interface IPredicateProps {
  rule: TConditionRule;
  ruleIndex: number;
  accessConditions: boolean;
  changeCurrentRule: (changedFields: Partial<TConditionRule>) => void;
  displayedVariable: IDropdownVariable | null;
  isDisabledOperator: boolean;
  selectedOperator: IDropdownOperator | null;
  dropdownOperators: IDropdownOperator[];
  selectedVariable?: IDropdownVariable | null;
  users?: TUserListItem[];
  handleRemoveRule: (conditionIndex?: number) => (ruleIndex: number) => () => void;
  conditionIndex?: number;
  isCheckIs?: boolean;
  options: {
    label: string;
    options: IDropdownVariable[];
  }[];
}

export function Predicate({
  rule,
  ruleIndex,
  accessConditions,
  changeCurrentRule,
  displayedVariable,
  isDisabledOperator,
  selectedOperator,
  dropdownOperators,
  selectedVariable,
  users,
  handleRemoveRule,
  conditionIndex,
  isCheckIs,
  options,
}: IPredicateProps) {
  const { formatMessage } = useIntl();

  return (
    <div key={`${rule.ruleApiName}-${rule.predicateApiName}`} className={styles['condition-rule']}>
      {ruleIndex !== 0 && (
        <div className={styles['condition-rule__logic-operation']}>
          {rule.logicOperation && (
            <SelectMenu
              isDisabled={!accessConditions}
              hideSelectedOption
              activeValue={rule.logicOperation}
              containerClassName={styles['select-logic-operation']}
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
            !accessConditions && styles['condition-rule__settings_disabled'],
          )}
        >
          <div className={classnames(styles['condition-rule__setting'], styles['condition-rule__field'])}>
            <DropdownList
              isDisabled={!accessConditions}
              placeholder={formatMessage({ id: 'templates.conditions.field-placeholder' })}
              isSearchable={false}
              value={displayedVariable}
              getOptionLabel={(option: IDropdownVariable) => option.richLabel}
              onChange={(option: IDropdownVariable) => {
                if (option.apiName === rule.field) return;

                const isStartingOrder = CONDITION_DISABLED_OPERATOR.find((val) => val === option.type);

                changeCurrentRule({
                  fieldType: option.type,
                  field: option.type !== 'kickoff' ? option.apiName : null,
                  value: isStartingOrder ? null : undefined,
                  operator: isStartingOrder ? EConditionOperators.Completed : undefined,
                });
              }}
              isClearable={false}
              options={options}
            />
          </div>
          {isCheckIs && (
            <div className={classnames(styles['condition-rule__setting'], styles['condition-rule__operator'])}>
              <DropdownList
                isDisabled={isDisabledOperator}
                placeholder={formatMessage({ id: 'templates.conditions.operator-placeholder' })}
                isSearchable={false}
                value={selectedOperator}
                onChange={(option: IDropdownOperator) => {
                  if (option.operator === rule.operator) return;

                  const shouldClearValue = OPERATORS_WITHOUT_VALUE.includes(option.operator);

                  changeCurrentRule({
                    operator: option.operator,
                    ...(shouldClearValue && { value: undefined }),
                  });
                }}
                isClearable={false}
                options={dropdownOperators}
                formatOptionLabel={(option: IDropdownOperator, { context }) =>
                  context === 'menu'
                    ? getFormattedDropdownOption({
                        label: option.label,
                        isSelected: option.operator === rule.operator,
                      })
                    : option.label
                }
              />
            </div>
          )}
          {isCheckIs && (
            <ConditionValueField
              isDisabled={!accessConditions}
              variable={selectedVariable || null}
              operator={selectedOperator?.operator}
              rule={rule}
              users={users || []}
              changeRuleValue={(value, kind) =>
                changeCurrentRule({ value, ...(kind ? { fieldType: kind as any } : {}) })
              }
            />
          )}
          <button
            type="button"
            aria-label={formatMessage({ id: 'templates.conditions.remove-condition-rule' })}
            onClick={handleRemoveRule(conditionIndex)(ruleIndex)}
            className={stylesTaskForm['taskform__remove-rule']}
          >
            <TrashIcon />
          </button>
        </div>
      </div>
    </div>
  );
}
