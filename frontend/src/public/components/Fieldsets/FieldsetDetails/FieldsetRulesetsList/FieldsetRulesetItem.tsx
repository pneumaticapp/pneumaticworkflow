import * as React from 'react';
import { useIntl } from 'react-intl';

import { EExtraFieldType } from '../../../../types/template';
import { EFieldRuleType } from '../../../../types/fieldset';

import { TFieldsetRulesetItemProps } from './types';
import {
  updateRulesetMessage,
  deleteRuleset,
  addGroupAndToRulesets,
  updateRuleInRulesets,
  deleteRuleFromRulesets,
  regroupRulesInRulesets,
} from './utils';
import {
  RulesetRuleList,
  RulesetMessageInput,
} from '../RuleBase';
import { RulesetFieldsSelector } from './RulesetFieldsSelector';

import styles from './FieldsetRulesets.css';

export const FieldsetRulesetItem = ({
  ruleSet,
  rulesets,
  fields,
  numericFields,
  onRulesetsChange,
  isReadOnly,
}: TFieldsetRulesetItemProps) => {
  const { formatMessage } = useIntl();

  return (
    <div className={styles['ruleset-card']}>
      <RulesetMessageInput
        message={ruleSet.message}
        onChange={(message) =>
          updateRulesetMessage({
            rulesets,
            rulesetApiName: ruleSet.apiName,
            message,
            onRulesetsChange,
          })
        }
        isReadOnly={isReadOnly}
      />

      <RulesetRuleList
        ruleSet={ruleSet}
        ruleType={EFieldRuleType.Validator}
        fieldType={EExtraFieldType.Number}
        isFieldsetRuleset
        isReadOnly={isReadOnly}
        addRule={() =>
          addGroupAndToRulesets({ rulesets, rulesetApiName: ruleSet.apiName, onRulesetsChange })
        }
        updateRule={(params) =>
          updateRuleInRulesets({
            ...params,
            rulesets,
            rulesetApiName: ruleSet.apiName,
            onRulesetsChange,
          })
        }
        deleteRule={(params) =>
          deleteRuleFromRulesets({
            ...params,
            rulesets,
            rulesetApiName: ruleSet.apiName,
            onRulesetsChange,
          })
        }
        regroupRules={(params) =>
          regroupRulesInRulesets({
            ...params,
            rulesets,
            rulesetApiName: ruleSet.apiName,
            onRulesetsChange,
          })
        }
      />

      <RulesetFieldsSelector
        ruleSet={ruleSet}
        rulesets={rulesets}
        fields={fields}
        numericFields={numericFields}
        onRulesetsChange={onRulesetsChange}
        isReadOnly={isReadOnly}
      />

      {!isReadOnly && (
        <div className={styles['ruleset-card__footer']}>
          <button
            type="button"
            className={styles['ruleset-card__delete-btn']}
            onClick={() =>
              deleteRuleset({ rulesets, rulesetApiName: ruleSet.apiName, onRulesetsChange })
            }
          >
            {formatMessage({ id: 'fieldsets.ruleset-delete' })}
          </button>
        </div>
      )}
    </div>
  );
};
