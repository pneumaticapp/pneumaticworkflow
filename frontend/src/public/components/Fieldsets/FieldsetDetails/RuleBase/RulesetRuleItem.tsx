import * as React from 'react';
import { useIntl } from 'react-intl';

import { SelectMenu } from '../../../UI';
import { TrashIcon } from '../../../icons';

import { EFieldRuleType } from '../../../../types/fieldset';
import { FIELDSET_RULE_COMBINATORS } from '../../constants';
import { getRuleCombinator } from './utils';
import { IRulesetRuleItemProps } from './types';
import { RuleItemFieldOperatorValue } from './RuleItemFieldOperatorValue';
import { RuleItemOperatorValue } from './RuleItemOperatorValue';

import styles from '../FieldsetRulesetsList/FieldsetRulesets.css';

export const RulesetRuleItem = ({
  groupAndRule,
  groupOrApiName,
  groupOrIndex,
  groupAndIndex,
  fieldRuleShowFieldOptions,
  ruleType,
  fieldType,
  selections,
  datasetId,
  isReadOnly,
  isFieldsetRuleset,
  updateRule,
  deleteRule,
  regroupRules,
}: IRulesetRuleItemProps) => {
  const { formatMessage } = useIntl();
  const { apiName: groupAndApiName } = groupAndRule;

  const isFirstRule = groupOrIndex === 0 && groupAndIndex === 0;
  const ruleCombinator = getRuleCombinator(groupAndIndex);
  const isShowRule = ruleType === EFieldRuleType.Show;

  return (
    <div className={styles['rule-item']}>
      {!isFirstRule && (
        <div className={styles['rule-item__combinator']}>
          <SelectMenu
            isDisabled={isReadOnly}
            hideSelectedOption
            activeValue={ruleCombinator}
            containerClassName={styles['select-rule-combinator']}
            toggleClassName={styles['select-toggle']}
            values={FIELDSET_RULE_COMBINATORS}
            onChange={(newCombinator) => {
              if (newCombinator !== ruleCombinator) {
                regroupRules({
                  groupOrApiName,
                  groupAndApiName,
                  ruleCombinator: newCombinator,
                });
              }
            }}
          />
        </div>
      )}
      <div className={styles['rule-row']}>
        {isShowRule ? (
          <RuleItemFieldOperatorValue
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            fieldRuleShowFieldOptions={fieldRuleShowFieldOptions || []}
            isReadOnly={isReadOnly}
            updateRule={updateRule}
          />
        ) : (
          <RuleItemOperatorValue
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            fieldType={fieldType}
            selections={selections}
            datasetId={datasetId}
            isReadOnly={isReadOnly}
            isFieldsetRuleset={isFieldsetRuleset}
            updateRule={updateRule}
          />
        )}

        {!isReadOnly && (
          <button
            type="button"
            aria-label={formatMessage({ id: 'fieldsets.rule-delete' })}
            className={styles['rule-remove-btn']}
            onClick={() => deleteRule({ groupOrApiName, groupAndApiName })}
          >
            <TrashIcon />
          </button>
        )}
      </div>
    </div>
  );
};
