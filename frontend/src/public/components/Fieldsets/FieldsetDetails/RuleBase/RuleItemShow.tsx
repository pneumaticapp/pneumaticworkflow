import * as React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { FilterSelect } from '../../../UI';
import { RuleOperatorSelect } from './RuleOperatorSelect';
import { RuleValueInput } from './RuleValueInput';
import {
  IFieldRuleShowFieldOption,
  IFieldRuleShowItemProps,
} from './types';
import { isOperatorWithoutValue } from './utils';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesetsList/FieldsetRulesets.css';

export const RuleItemShow = ({
  groupAndRule,
  groupOrApiName,
  fieldRuleShowFieldOptions,
  isReadOnly,
  updateRule,
}: IFieldRuleShowItemProps) => {
  const { formatMessage } = useIntl();
  const { apiName: groupAndApiName, operator, value, field: fieldApiName } = groupAndRule;

  const fieldPlaceholderText = formatMessage({ id: 'fieldsets.field-rule.select-field-placeholder' });

  const selectedFieldOption = fieldRuleShowFieldOptions.find((option) => option.apiName === fieldApiName);
  const selectedFieldLabel = selectedFieldOption?.name || '';

  const isFieldSelectDisabled = isReadOnly;
  const isWithoutValue = isOperatorWithoutValue(operator);

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

      <RuleOperatorSelect
        fieldType={selectedFieldOption?.type}
        operator={operator}
        isReadOnly={isReadOnly}
        onChange={(newOperator) => {
          updateRule({
            groupOrApiName,
            groupAndApiName,
            ruleChanges: {
              operator: newOperator,
              ...(isOperatorWithoutValue(newOperator) ? { value: '' } : {}),
            },
          });
        }}
      />

      {Boolean(operator) && !isWithoutValue && (
        <RuleValueInput
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
