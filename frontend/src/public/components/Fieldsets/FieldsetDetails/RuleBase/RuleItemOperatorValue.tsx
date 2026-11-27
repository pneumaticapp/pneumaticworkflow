import * as React from 'react';
import { RuleOperatorSelect } from './RuleOperatorSelect';
import { RuleValueInput } from './RuleValueInput';
import type { IRuleItemOperatorValueProps } from './types';
import { isOperatorWithoutValue } from './utils';

export const RuleItemOperatorValue = ({
  groupAndRule,
  groupOrApiName,
  fieldType,
  selections,
  datasetId,
  isReadOnly,
  isFieldsetRuleset,
  updateRule,
}: IRuleItemOperatorValueProps) => {
  const { apiName: groupAndApiName, operator, value, valueType } = groupAndRule;

  const isWithoutValue = isOperatorWithoutValue(operator);

  return (
    <>
      <RuleOperatorSelect
        fieldType={fieldType}
        operator={operator}
        isFieldsetRuleset={isFieldsetRuleset}
        isReadOnly={isReadOnly}
        onChange={(newOperator) => {
          updateRule({
            groupOrApiName,
            groupAndApiName,
            ruleChanges: {
              operator: newOperator,
              ...(isOperatorWithoutValue(newOperator) ? { value: '', ...(valueType && { valueType: null }) } : {}),
            },
          });
        }}
      />

      {Boolean(operator) && !isWithoutValue && (
        <RuleValueInput
          fieldType={fieldType}
          value={value}
          valueType={valueType}
          selections={selections}
          datasetId={datasetId}
          isReadOnly={isReadOnly}
          onChange={(selectedValue, selectedValueType) => {
            updateRule({
              groupOrApiName,
              groupAndApiName,
              ruleChanges: {
                value: selectedValue,
                ...(selectedValueType !== undefined && { valueType: selectedValueType }),
              },
            });
          }}
        />
      )}
    </>
  );
};
