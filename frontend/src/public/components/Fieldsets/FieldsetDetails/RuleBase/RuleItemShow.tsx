import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import classnames from 'classnames';

import { FilterSelect } from '../../../UI';
import { EExtraFieldType } from '../../../../types/template';
import { getFieldsetRuleShowOperators } from './utils';
import { FieldsetFieldRulesValue } from './RuleValueField';
import { TRuleFieldOption, TRuleOperatorOption, TRuleItemShowProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleItemShow = ({
  groupAndRule,
  groupOrApiName,
  ruleOperatorOptions,
  rulesFieldOptions,
  isReadOnly,
  updateRule,
}: TRuleItemShowProps) => {
  const { formatMessage, messages } = useIntl();
  const { apiName: groupAndApiName, operator, value, field: fieldApiName } = groupAndRule;

  const fieldPlaceholderText = formatMessage({ id: 'fieldsets.field-rule.select-field-placeholder' });
  const operatorPlaceholderText = formatMessage({ id: 'templates.conditions.operator-placeholder' });

  const selectedFieldOption = rulesFieldOptions.find((option) => option.apiName === fieldApiName);
  const selectedFieldLabel = selectedFieldOption?.name || '';
  const isFileField = selectedFieldOption?.type === EExtraFieldType.File;

  const fieldOperatorOptions = useMemo(() => {
    if (selectedFieldOption?.type) {
      return getFieldsetRuleShowOperators(
        selectedFieldOption.type,
        messages as Record<string, string>,
      );
    }
    return ruleOperatorOptions;
  }, [selectedFieldOption?.type, messages, ruleOperatorOptions]);

  const selectedOperatorLabel =
    fieldOperatorOptions.find((option) => option.apiName === operator)?.name || '';

  const isFieldSelectDisabled = isReadOnly;

  return (
    <>
      <FilterSelect<'apiName', 'name', TRuleFieldOption>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={rulesFieldOptions}
        selectedOption={fieldApiName || ''}
        onChange={(key) => {
          if (key && key !== fieldApiName) {
            updateRule({
              ruleGroupOrApiName: groupOrApiName,
              ruleGroupAndApiName: groupAndApiName,
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

      {!isFileField && (
        <>
          <FilterSelect<'apiName', 'name', TRuleOperatorOption>
            optionIdKey="apiName"
            optionLabelKey="name"
            options={fieldOperatorOptions}
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

          {Boolean(operator) && (
            <FieldsetFieldRulesValue
              fieldType={selectedFieldOption?.type}
              value={value}
              selections={selectedFieldOption?.selections}
              isReadOnly={isReadOnly}
              onChange={(newValue) =>
                updateRule({
                  ruleGroupOrApiName: groupOrApiName,
                  ruleGroupAndApiName: groupAndApiName,
                  ruleChanges: { value: newValue },
                })
              }
            />
          )}
        </>
      )}
    </>
  );
};
