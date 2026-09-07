import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { FilterSelect } from '../../../UI';
import { getRuleOperators } from './utils';
import {
  IFieldRuleBaseOperatorOption,
  IRuleOperatorSelectProps,
} from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleOperatorSelect = ({
  fieldType,
  operator,
  isReadOnly,
  isFieldsetRuleset,
  onChange,
}: IRuleOperatorSelectProps) => {
  const { formatMessage } = useIntl();
  const operatorPlaceholderText = formatMessage({ id: 'templates.conditions.operator-placeholder' });

  const fieldOperatorOptions = useMemo(() => {
    if (fieldType) {
      return getRuleOperators(fieldType, formatMessage, isFieldsetRuleset);
    }
    return [];
  }, [fieldType, formatMessage, isFieldsetRuleset]);

  const selectedOperatorLabel =
    fieldOperatorOptions.find((option) => option.apiName === operator)?.name || '';

  return (
    <FilterSelect<'apiName', 'name', IFieldRuleBaseOperatorOption>
      optionIdKey="apiName"
      optionLabelKey="name"
      options={fieldOperatorOptions}
      selectedOption={operator || ''}
      onChange={(key) => {
        if (key && key !== operator) {
          onChange(String(key));
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
  );
};
