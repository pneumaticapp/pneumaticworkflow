import * as React from 'react';
import { useIntl } from 'react-intl';

import { SelectMenu } from '../../../UI';
import { TrashIcon } from '../../../icons';

import { EFieldRuleType } from '../../../../types/fieldset';
import { FIELDSET_RULE_COMBINATORS } from '../../constants';
import { getRuleCombinator } from './utils';
import { IFieldRuleBaseItemProps } from './types';
import { RuleItemShow } from './RuleItemShow';
import { RuleItemValidator } from './RuleItemValidator';

import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RuleItem = ({
  groupAndRule,
  groupOrApiName,
  groupOrIndex,
  groupAndIndex,
  fieldRuleBaseOperatorOptions,
  fieldRuleShowFieldOptions,
  ruleType,
  isReadOnly,
  updateRule,
  deleteRule,
  regroupRules,
}: IFieldRuleBaseItemProps) => {
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
          <RuleItemShow
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            fieldRuleBaseOperatorOptions={fieldRuleBaseOperatorOptions}
            fieldRuleShowFieldOptions={fieldRuleShowFieldOptions || []}
            isReadOnly={isReadOnly}
            updateRule={updateRule}
          />
        ) : (
          <RuleItemValidator
            groupAndRule={groupAndRule}
            groupOrApiName={groupOrApiName}
            fieldRuleBaseOperatorOptions={fieldRuleBaseOperatorOptions}
            isReadOnly={isReadOnly}
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
