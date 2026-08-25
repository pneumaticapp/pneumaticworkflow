import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { FIELDSET_RULE_OPERATOR_OPTIONS } from '../../constants';
import { TRuleListProps } from './types';
import { RuleItem } from './RuleItem';

import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleList = ({
  ruleSet,
  isReadOnly,
  addRule,
  updateRule,
  deleteRule,
  regroupRules,
}: TRuleListProps) => {
  const { formatMessage } = useIntl();

  const ruleOperatorOptions = useMemo(
    () =>
      FIELDSET_RULE_OPERATOR_OPTIONS.map((operatorOption) => ({
        apiName: operatorOption.value,
        name: formatMessage({ id: operatorOption.labelKey }),
      })),
    [formatMessage],
  );

  const { groupsOr = [] } = ruleSet;

  return (
    <>
      <span className={styles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.rules' })}
      </span>

      {groupsOr.map(({ apiName: groupOrApiName, groupsAnd = [] }, groupOrIndex) =>
        groupsAnd.map((groupAndRule, groupAndIndex) => (
          <RuleItem
            key={groupAndRule.apiName}
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            groupOrIndex={groupOrIndex}
            groupAndIndex={groupAndIndex}
            ruleOperatorOptions={ruleOperatorOptions}
            isReadOnly={isReadOnly}
            updateRule={updateRule}
            deleteRule={deleteRule}
            regroupRules={regroupRules}
          />
        )),
      )}

      {!isReadOnly && (
        <button
          type="button"
          className={styles['add-rule-btn']}
          onClick={addRule}
        >
          {formatMessage({
            id: groupsOr.length > 0 ? 'fieldsets.add-another-rule' : 'fieldsets.add-rule',
          })}
        </button>
      )}
    </>
  );
};
