import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import classnames from 'classnames';

import { FilterSelect } from '../../../UI';
import { getFieldRuleShowOperators } from './utils';
import { FieldsetFieldRulesValue } from './RuleValueField';
import {
  IFieldRuleShowFieldOption,
  IFieldRuleBaseOperatorOption,
  IFieldRuleShowItemProps,
  FIELD_RULE_SHOW_OPERATORS_WITHOUT_VALUE,
  EFieldRuleShowOperator,
} from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleItemShow = ({
  groupAndRule,
  groupOrApiName,
  fieldRuleBaseOperatorOptions,
  fieldRuleShowFieldOptions,
  isReadOnly,
  updateRule,
}: IFieldRuleShowItemProps) => {
  const { formatMessage, messages } = useIntl();
  const { apiName: groupAndApiName, operator, value, field: fieldApiName } = groupAndRule;

  const fieldPlaceholderText = formatMessage({ id: 'fieldsets.field-rule.select-field-placeholder' });
  const operatorPlaceholderText = formatMessage({ id: 'templates.conditions.operator-placeholder' });

  const selectedFieldOption = fieldRuleShowFieldOptions.find((option) => option.apiName === fieldApiName);
  const selectedFieldLabel = selectedFieldOption?.name || '';

  const fieldOperatorOptions = useMemo(() => {
    if (selectedFieldOption?.type) {
      return getFieldRuleShowOperators(
        selectedFieldOption.type,
        messages as Record<string, string>,
      );
    }
    return fieldRuleBaseOperatorOptions;
  }, [selectedFieldOption?.type, messages, fieldRuleBaseOperatorOptions]);

  const selectedOperatorLabel =
    fieldOperatorOptions.find((option) => option.apiName === operator)?.name || '';

  const isFieldSelectDisabled = isReadOnly;
  const isOperatorWithoutValue = FIELD_RULE_SHOW_OPERATORS_WITHOUT_VALUE.includes(
    operator as EFieldRuleShowOperator,
  );

  return (
    <>
      <FilterSelect<'apiName', 'name', IFieldRuleShowFieldOption>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={fieldRuleShowFieldOptions}
        selectedOption={fieldApiName || ''}
        onChange={(key) => {
          if (key && key !== fieldApiName) {
            updateRule({
              groupOrApiName,
              groupAndApiName,
              ruleChanges: {
                field: String(key),
                operator: null,
                value: '',
              },
            });
          }
        }}
        resetFilter={() => {}}
        placeholderText={fieldPlaceholderText}
        isDisabled={isFieldSelectDisabled}
        containerClassname={classnames(
          fieldsetDetailsStyles['rule-operator-select'],
          styles['rule-field-select'],
        )}
        toggleClassName={fieldsetDetailsStyles['rule-operator-select__toggle']}
        menuClassName={fieldsetDetailsStyles['rule-operator-select__menu']}
        renderPlaceholder={() =>
          selectedFieldLabel || <span className={styles['rule-select-placeholder']}>{fieldPlaceholderText}</span>
        }
      />

      <FilterSelect<'apiName', 'name', IFieldRuleBaseOperatorOption>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={fieldOperatorOptions}
        selectedOption={operator}
        onChange={(key) => {
          if (key && key !== operator) {
            const isNewOperatorWithoutValue = FIELD_RULE_SHOW_OPERATORS_WITHOUT_VALUE.includes(key as EFieldRuleShowOperator);
            updateRule({
              groupOrApiName,
              groupAndApiName,
              ruleChanges: {
                operator: String(key),
                ...(isNewOperatorWithoutValue ? { value: '' } : {}),
              },
            });
          }
        }}
        resetFilter={() => {}}
        placeholderText={operatorPlaceholderText}
        isDisabled={isReadOnly}
        containerClassname={classnames(
          fieldsetDetailsStyles['rule-operator-select'],
          styles['rule-operator-select'],
        )}
        toggleClassName={fieldsetDetailsStyles['rule-operator-select__toggle']}
        menuClassName={fieldsetDetailsStyles['rule-operator-select__menu']}
        renderPlaceholder={() =>
          selectedOperatorLabel || <span className={styles['rule-select-placeholder']}>{operatorPlaceholderText}</span>
        }
      />

      {Boolean(operator) && !isOperatorWithoutValue && (
        <FieldsetFieldRulesValue
          fieldType={selectedFieldOption?.type}
          value={value}
          selections={selectedFieldOption?.selections}
          datasetId={selectedFieldOption?.datasetId}
          isReadOnly={isReadOnly}
          onChange={(newValue) =>
            updateRule({
              groupOrApiName,
              groupAndApiName,
              ruleChanges: { value: newValue },
            })
          }
        />
      )}
    </>
  );
};
