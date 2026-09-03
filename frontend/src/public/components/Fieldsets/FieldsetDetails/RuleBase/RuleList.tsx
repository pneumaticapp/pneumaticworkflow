import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { IFieldRuleBaseListProps } from './types';
import { RuleItem } from './RuleItem';

import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleList = ({
  ruleSet,
  operatorOptions,
  fieldRuleShowFieldOptions,
  ruleType,
  fieldType,
  selections,
  datasetId,
  isReadOnly,
  addRule,
  updateRule,
  deleteRule,
  regroupRules,
}: IFieldRuleBaseListProps) => {
  const { formatMessage } = useIntl();

  const fieldRuleBaseOperatorOptions = useMemo(
    () =>
      operatorOptions.map((operatorOption) => ({
        apiName: operatorOption.value,
        name: formatMessage({ id: operatorOption.labelKey }),
      })),
    [formatMessage, operatorOptions],
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
            fieldRuleBaseOperatorOptions={fieldRuleBaseOperatorOptions}
            fieldRuleShowFieldOptions={fieldRuleShowFieldOptions}
            ruleType={ruleType}
            fieldType={fieldType}
            selections={selections}
            datasetId={datasetId}
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
