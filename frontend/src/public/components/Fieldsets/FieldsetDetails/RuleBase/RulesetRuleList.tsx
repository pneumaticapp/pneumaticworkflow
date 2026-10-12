import * as React from 'react';
import { useIntl } from 'react-intl';

import { IRulesetRuleListProps } from './types';
import { RulesetRuleItem } from './RulesetRuleItem';

import styles from '../FieldsetRulesetsList/FieldsetRulesets.css';

export const RulesetRuleList = ({
  ruleSet,
  fieldRuleShowFieldOptions,
  ruleType,
  fieldType,
  selections,
  datasetId,
  isReadOnly,
  isFieldsetRuleset,
  addRule,
  updateRule,
  deleteRule,
  regroupRules,
}: IRulesetRuleListProps) => {
  const { formatMessage } = useIntl();

  const { groupsOr } = ruleSet;

  return (
    <>
      <span className={styles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.rules' })}
      </span>

      {groupsOr.map(({ apiName: groupOrApiName, groupsAnd }, groupOrIndex) =>
        groupsAnd.map((groupAndRule, groupAndIndex) => (
          <RulesetRuleItem
            key={groupAndRule.apiName}
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            groupOrIndex={groupOrIndex}
            groupAndIndex={groupAndIndex}
            fieldRuleShowFieldOptions={fieldRuleShowFieldOptions}
            ruleType={ruleType}
            fieldType={fieldType}
            selections={selections}
            datasetId={datasetId}
            isReadOnly={isReadOnly}
            isFieldsetRuleset={isFieldsetRuleset}
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
