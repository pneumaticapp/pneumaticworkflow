import * as React from 'react';
import { RuleOperatorSelect } from './RuleOperatorSelect';
import { RuleValueInput } from './RuleValueInput';
import {
  IFieldRuleValidatorItemProps,
  FIELD_RULE_SHOW_OPERATORS_WITHOUT_VALUE,
  EFieldRuleShowOperator,
} from './types';

export const RuleItemValidator = ({
  groupAndRule,
  groupOrApiName,
  fieldType,
  selections,
  datasetId,
  isReadOnly,
  updateRule,
}: IFieldRuleValidatorItemProps) => {
  const { apiName: groupAndApiName, operator, value } = groupAndRule;

  const isOperatorWithoutValue = FIELD_RULE_SHOW_OPERATORS_WITHOUT_VALUE.includes(
    operator as EFieldRuleShowOperator,
  );

  return (
    <>
      <RuleOperatorSelect
        fieldType={fieldType}
        operator={operator}
        isReadOnly={isReadOnly}
        onChange={(newOperator, isWithoutValue) => {
          updateRule({
            groupOrApiName,
            groupAndApiName,
            ruleChanges: {
              operator: newOperator,
              ...(isWithoutValue ? { value: '' } : {}),
            },
          });
        }}
      />

      {Boolean(operator) && !isOperatorWithoutValue && (
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
