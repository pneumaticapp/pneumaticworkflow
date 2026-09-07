import * as React from 'react';
import { RuleOperatorSelect } from './RuleOperatorSelect';
import { RuleValueInput } from './RuleValueInput';
import { IFieldRuleValidatorItemProps } from './types';
import { isOperatorWithoutValue } from './utils';

export const RuleItemValidator = ({
  groupAndRule,
  groupOrApiName,
  fieldType,
  selections,
  datasetId,
  isReadOnly,
  isFieldsetRuleset,
  updateRule,
}: IFieldRuleValidatorItemProps) => {
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

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
              ...(isOperatorWithoutValue(newOperator) ? { value: '' } : {}),
            },
          });
        }}
      />

      {Boolean(operator) && !isWithoutValue && (
        <RuleValueInput
          fieldType={fieldType}
          value={value}
          selections={selections}
          datasetId={datasetId}
          isReadOnly={isReadOnly}
          onChange={(newValue) => {
            updateRule({
              groupOrApiName,
              groupAndApiName,
              ruleChanges: { value: newValue },
            });
          }}
        />
      )}
    </>
  );
};
