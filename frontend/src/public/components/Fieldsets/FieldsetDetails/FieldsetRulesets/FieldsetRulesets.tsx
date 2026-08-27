import * as React from 'react';
import { useIntl } from 'react-intl';

import { EExtraFieldType } from '../../../../types/template';
import { EFieldRuleType } from '../../../../types/fieldset';

import { TFieldsetRulesetsProps } from './types';
import { FIELDSET_RULE_OPERATOR_OPTIONS } from '../../constants';
import {
  updateRulesetMessage,
  deleteRuleset,
  addRuleset,
  addGroupAndToRulesets,
  updateRuleInRulesets,
  deleteRuleFromRulesets,
  regroupRulesInRulesets,
} from './utils';
import { RuleList, RulesetMessageInput } from '../RuleBase';
import { RulesetFieldsSelector } from './RulesetFieldsSelector';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from './FieldsetRulesets.css';

export const FieldsetRulesets = ({
  rulesets,
  fields,
  onRulesetsChange,
  isReadOnly,
}: TFieldsetRulesetsProps) => {
  const { formatMessage } = useIntl();

  const numericFields = fields.filter((field) => field.type === EExtraFieldType.Number);

  return (
    <div className={fieldsetDetailsStyles['list']}>
      <h2 className={fieldsetDetailsStyles['section-title']}>
        {formatMessage({ id: 'fieldsets.rules-section' })}
        {isReadOnly && (
          <span className={fieldsetDetailsStyles['readonly-badge']}>
            {formatMessage({ id: 'fieldsets.readonly-badge' })}
          </span>
        )}
      </h2>

      {rulesets.length === 0 && (
        <p className={fieldsetDetailsStyles['empty-text']}>{formatMessage({ id: 'fieldsets.no-rules' })}</p>
      )}

      {rulesets.map((ruleSet) => (
        <div key={ruleSet.apiName} className={styles['ruleset-card']}>
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

          <RuleList
            ruleSet={ruleSet}
            ruleType={EFieldRuleType.Validator}
            operatorOptions={FIELDSET_RULE_OPERATOR_OPTIONS}
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
      ))}

      {!isReadOnly && (
        <button
          type="button"
          className={styles['add-ruleset-btn']}
          onClick={() => addRuleset({ rulesets, onRulesetsChange })}
        >
          + {formatMessage({ id: 'fieldsets.add-ruleset' })}
        </button>
      )}
    </div>
  );
};
