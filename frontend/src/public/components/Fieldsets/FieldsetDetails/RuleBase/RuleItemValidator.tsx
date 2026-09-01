import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { NumericFormat } from 'react-number-format';

import { FilterSelect } from '../../../UI';
import { IFieldRuleBaseOperatorOption, IFieldRuleValidatorItemProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleItemValidator = ({
  groupAndRule,
  groupOrApiName,
  fieldRuleBaseOperatorOptions,
  isReadOnly,
  updateRule,
}: IFieldRuleValidatorItemProps) => {
  const { formatMessage } = useIntl();
  const [isTouched, setIsTouched] = useState(false);
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

  useEffect(() => {
    setIsTouched(false);
  }, [value, operator]);

  const selectedValidatorOperatorOption =
    fieldRuleBaseOperatorOptions.find((option) => option.apiName === operator) || fieldRuleBaseOperatorOptions[0];

  const selectedValidatorOperatorLabel = selectedValidatorOperatorOption?.name || '';
  const currentValidatorOperator = selectedValidatorOperatorOption?.apiName || '';

  const isValueError = isTouched && (!value || !value.trim());

  return (
    <>
      <FilterSelect<'apiName', 'name', IFieldRuleBaseOperatorOption>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={fieldRuleBaseOperatorOptions}
        selectedOption={currentValidatorOperator}
        onChange={(key) => {
          if (key && key !== operator) {
            updateRule({
              groupOrApiName,
              groupAndApiName,
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
            groupOrApiName,
            groupAndApiName,
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
