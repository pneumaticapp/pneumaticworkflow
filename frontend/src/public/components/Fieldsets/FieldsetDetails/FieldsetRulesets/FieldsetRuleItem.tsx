import * as React from 'react';
import { useIntl } from 'react-intl';

import { FilterSelect, SelectMenu } from '../../../UI';
import { TrashIcon } from '../../../icons';

import { EFieldsetNumberRulesetOperator } from '../../../../types/fieldset';
import { FIELDSET_RULE_COMBINATORS } from '../../constants';

import { TRulePath, TFieldsetRuleItemProps } from './types';
import {
  getRuleCombinator,
  regroupRules,
  updateRuleset,
  deleteRule,
} from './utils';

import styles from '../FieldsetDetails.css';

export const FieldsetRuleItem = ({
  groupAndRule,
  groupOrApiName,
  groupOrIndex,
  groupAndIndex,
  rulesetApiName,
  rulesets,
  ruleOperatorOptions,
  isReadOnly,
  onRulesetsChange,
}: TFieldsetRuleItemProps) => {
  const { formatMessage } = useIntl();
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

  const rulePath: TRulePath = {
    rulesetApiName,
    ruleGroupOrApiName: groupOrApiName,
    ruleGroupAndApiName: groupAndApiName,
  };

  const isFirstRule = groupOrIndex === 0 && groupAndIndex === 0;
  const ruleCombinator = getRuleCombinator(groupAndIndex);
  const ruleOperator = operator || EFieldsetNumberRulesetOperator.SumEqual;

  const selectedOperatorLabel =
    ruleOperatorOptions.find((option) => option.apiName === ruleOperator)?.name || '';

  return (
    <div className={styles['rule-item']}>
      {!isFirstRule && (
        <div className={styles['rule-item__combinator']}>
          <SelectMenu
            isDisabled={isReadOnly}
            hideSelectedOption
            activeValue={ruleCombinator}
            containerClassName={styles['select-rule-combinator']}
            toggleClassName={styles['select-toggle']}
            values={FIELDSET_RULE_COMBINATORS}
            onChange={(newCombinator) => {
              if (newCombinator !== ruleCombinator) {
                regroupRules({
                  rulesets,
                  rulesetApiName,
                  groupOrApiName,
                  groupAndApiName,
                  ruleCombinator: newCombinator,
                  onRulesetsChange,
                });
              }
            }}
          />
        </div>
      )}
      <div className={styles['rule-row']}>
        <FilterSelect<'apiName', 'name', { apiName: EFieldsetNumberRulesetOperator; name: string }>
          optionIdKey="apiName"
          optionLabelKey="name"
          options={ruleOperatorOptions}
          selectedOption={ruleOperator}
          onChange={(key) => {
            if (key && key !== operator) {
              updateRuleset({
                rulesets,
                rulePath,
                ruleChanges: {
                  operator: key as EFieldsetNumberRulesetOperator,
                },
                onRulesetsChange,
              });
            }
          }}
          resetFilter={() => {}}
          placeholderText={formatMessage({ id: 'fieldsets.rule-operator-placeholder' })}
          isDisabled={isReadOnly}
          containerClassname={styles['rule-operator-select']}
          toggleClassName={styles['rule-operator-select__toggle']}
          menuClassName={styles['rule-operator-select__menu']}
          renderPlaceholder={() => selectedOperatorLabel}
        />

        <input
          type="text"
          className={styles['rule-value-input']}
          value={value}
          placeholder={formatMessage({ id: 'fieldsets.rule-value-placeholder-number' })}
          onChange={(e) =>
            updateRuleset({
              rulesets,
              rulePath,
              ruleChanges: { value: e.target.value },
              onRulesetsChange,
            })
          }
          disabled={isReadOnly}
        />

        {!isReadOnly && (
          <button
            type="button"
            aria-label={formatMessage({ id: 'fieldsets.rule-delete' })}
            className={styles['rule-remove-btn']}
            onClick={() => deleteRule({ rulesets, rulePath, onRulesetsChange })}
          >
            <TrashIcon />
          </button>
        )}
      </div>
    </div>
  );
};
