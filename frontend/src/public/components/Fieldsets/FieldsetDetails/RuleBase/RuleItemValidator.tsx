import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { NumericFormat } from 'react-number-format';

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
  const [isTouched, setIsTouched] = useState(false);
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

  useEffect(() => {
    setIsTouched(false);
  }, [value, operator]);

  const selectedValidatorOperatorOption =
    ruleOperatorOptions.find((option) => option.apiName === operator) || ruleOperatorOptions[0];

  const selectedValidatorOperatorLabel = selectedValidatorOperatorOption?.name || '';
  const currentValidatorOperator = selectedValidatorOperatorOption?.apiName || '';

  const isValueError = isTouched && (!value || !value.trim());

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

      <NumericFormat
        value={value}
        onValueChange={(values) => {
          updateRule({
            ruleGroupOrApiName: groupOrApiName,
            ruleGroupAndApiName: groupAndApiName,
            ruleChanges: { value: values.value },
          });
        }}
        onFocus={() => setIsTouched(false)}
        onBlur={() => setIsTouched(true)}
        allowNegative
        decimalSeparator="."
        thousandSeparator={false}
        allowedDecimalSeparators={['.', ',']}
        disabled={isReadOnly}
        placeholder={formatMessage({ id: 'fieldsets.rule-value-placeholder-number' })}
        className={classnames(styles['rule-value-input'], {
          [styles['rule-value-input_error']]: isValueError,
        })}
      />
    </>
  );
};
