import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { FIELDSET_RULE_OPERATOR_OPTIONS } from '../../constants';
import { TFieldsetRulesListProps } from './types';
import { FieldsetRuleItem } from './FieldsetRuleItem';
import { addGroupAnd } from './utils';

import styles from './FieldsetRulesets.css';

export const FieldsetRulesList = ({
  ruleSet,
  rulesets,
  onRulesetsChange,
  isReadOnly,
}: TFieldsetRulesListProps) => {
  const { formatMessage } = useIntl();

  const ruleOperatorOptions = useMemo(
    () =>
      FIELDSET_RULE_OPERATOR_OPTIONS.map((operatorOption) => ({
        apiName: operatorOption.value,
        name: formatMessage({ id: operatorOption.labelKey }),
      })),
    [formatMessage],
  );

  const { apiName: rulesetApiName, groupsOr = [] } = ruleSet;

  return (
    <>
      <span className={styles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.rules' })}
      </span>

      {groupsOr.map(({ apiName: groupOrApiName, groupsAnd = [] }, groupOrIndex) =>
        groupsAnd.map((groupAndRule, groupAndIndex) => (
          <FieldsetRuleItem
            key={groupAndRule.apiName}
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            groupOrIndex={groupOrIndex}
            groupAndIndex={groupAndIndex}
            rulesetApiName={rulesetApiName}
            rulesets={rulesets}
            ruleOperatorOptions={ruleOperatorOptions}
            isReadOnly={isReadOnly}
            onRulesetsChange={onRulesetsChange}
          />
        )),
      )}

      {!isReadOnly && (
        <button
          type="button"
          className={styles['add-rule-btn']}
          onClick={() => addGroupAnd({ rulesets, rulesetApiName, onRulesetsChange })}
        >
          {formatMessage({
            id: groupsOr.length > 0 ? 'fieldsets.add-another-rule' : 'fieldsets.add-rule',
          })}
        </button>
      )}
    </>
  );
};
