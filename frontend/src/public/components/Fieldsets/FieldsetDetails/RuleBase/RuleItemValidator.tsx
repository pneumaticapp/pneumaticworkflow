import * as React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { FilterSelect } from '../../../UI';
import { TRuleOperatorOption, TRuleItemValidatorProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleItemValidator = ({
  groupAndRule,
  groupOrApiName,
  ruleOperatorOptions,
  isReadOnly,
  updateRule,
}: TRuleItemValidatorProps) => {
  const { formatMessage } = useIntl();
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

  const selectedValidatorOperatorOption =
    ruleOperatorOptions.find((option) => option.apiName === operator) || ruleOperatorOptions[0];

  const selectedValidatorOperatorLabel = selectedValidatorOperatorOption?.name || '';
  const currentValidatorOperator = selectedValidatorOperatorOption?.apiName || '';

  return (
    <>
      <FilterSelect<'apiName', 'name', TRuleOperatorOption>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={ruleOperatorOptions}
        selectedOption={currentValidatorOperator}
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
        placeholderText=""
        isDisabled={isReadOnly}
        containerClassname={classnames(
          fieldsetDetailsStyles['rule-operator-select'],
          styles['rule-operator-select'],
        )}
        toggleClassName={fieldsetDetailsStyles['rule-operator-select__toggle']}
        menuClassName={fieldsetDetailsStyles['rule-operator-select__menu']}
        renderPlaceholder={() => selectedValidatorOperatorLabel}
      />

      <input
        type="text"
        className={styles['rule-value-input']}
        value={value}
        placeholder={formatMessage({ id: 'fieldsets.rule-value-placeholder-number' })}
        onChange={(event) =>
          updateRule({
            ruleGroupOrApiName: groupOrApiName,
            ruleGroupAndApiName: groupAndApiName,
            ruleChanges: { value: event.target.value },
          })
        }
        disabled={isReadOnly}
      />
    </>
  );
};
