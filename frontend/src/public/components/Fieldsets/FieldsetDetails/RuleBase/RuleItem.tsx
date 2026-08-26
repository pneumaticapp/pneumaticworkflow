import * as React from 'react';
import { useIntl } from 'react-intl';

import { FilterSelect, SelectMenu } from '../../../UI';
import { TrashIcon } from '../../../icons';

import { FIELDSET_RULE_COMBINATORS } from '../../constants';
import { getRuleCombinator } from './utils';
import { TRuleItemProps, TRuleOperatorOption } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleItem = ({
  groupAndRule,
  groupOrApiName,
  groupOrIndex,
  groupAndIndex,
  ruleOperatorOptions,
  isReadOnly,
  updateRule,
  deleteRule,
  regroupRules,
}: TRuleItemProps) => {
  const { formatMessage } = useIntl();
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

  const isFirstRule = groupOrIndex === 0 && groupAndIndex === 0;
  const ruleCombinator = getRuleCombinator(groupAndIndex);

  const selectedOperatorLabel =
    ruleOperatorOptions.find((option) => option.apiName === operator)?.name || '';

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
                  groupOrApiName,
                  groupAndApiName,
                  ruleCombinator: newCombinator,
                });
              }
            }}
          />
        </div>
      )}
      <div className={styles['rule-row']}>
        <FilterSelect<'apiName', 'name', TRuleOperatorOption>
          optionIdKey="apiName"
          optionLabelKey="name"
          options={ruleOperatorOptions}
          selectedOption={operator}
          onChange={(key) => {
            if (key && key !== operator) {
              updateRule({
                ruleGroupOrApiName: groupOrApiName,
                ruleGroupAndApiName: groupAndApiName,
                ruleChanges: {
                  operator: String(key),
                },
              });
            }
          }}
          resetFilter={() => {}}
          placeholderText={formatMessage({ id: 'fieldsets.rule-operator-placeholder' })}
          isDisabled={isReadOnly}
          containerClassname={fieldsetDetailsStyles['rule-operator-select']}
          toggleClassName={fieldsetDetailsStyles['rule-operator-select__toggle']}
          menuClassName={fieldsetDetailsStyles['rule-operator-select__menu']}
          renderPlaceholder={() => selectedOperatorLabel}
        />

        <input
          type="text"
          className={styles['rule-value-input']}
          value={value}
          placeholder={formatMessage({ id: 'fieldsets.rule-value-placeholder-number' })}
          onChange={(e) =>
            updateRule({
              ruleGroupOrApiName: groupOrApiName,
              ruleGroupAndApiName: groupAndApiName,
              ruleChanges: { value: e.target.value },
            })
          }
          disabled={isReadOnly}
        />

        {!isReadOnly && (
          <button
            type="button"
            aria-label={formatMessage({ id: 'fieldsets.rule-delete' })}
            className={styles['rule-remove-btn']}
            onClick={() => deleteRule({ ruleGroupOrApiName: groupOrApiName, ruleGroupAndApiName: groupAndApiName })}
          >
            <TrashIcon />
          </button>
        )}
      </div>
    </div>
  );
};
