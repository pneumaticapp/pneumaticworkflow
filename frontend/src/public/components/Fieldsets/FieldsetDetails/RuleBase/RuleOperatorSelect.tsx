import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { DropdownList } from '../../../UI';
import { getRuleOperators } from './utils';
import {
  IFieldRuleBaseOperatorOption,
  IRuleOperatorSelectProps,
} from './types';

import styles from '../FieldsetRulesetsList/FieldsetRulesets.css';

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

  const selectedOption = fieldOperatorOptions.find((option) => option.apiName === operator) || null;

  return (
    <DropdownList
      className={styles['rule-operator-select']}
      isDisabled={isReadOnly}
      placeholder={operatorPlaceholderText}
      isSearchable={false}
      value={selectedOption}
      onChange={(option: IFieldRuleBaseOperatorOption | null) => {
        if (option && option.apiName !== operator) {
          onChange(option.apiName);
        }
      }}
      isClearable={false}
      options={fieldOperatorOptions}
      classNames={{
        menu: () => styles['rule-operator-select__menu'],
        option: ({ isSelected }: { isSelected: boolean }) =>
          classnames(isSelected && styles['rule-operator-select__option_selected']),
      }}
    />
  );
};
