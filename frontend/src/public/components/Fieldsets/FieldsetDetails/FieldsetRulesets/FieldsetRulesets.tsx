import * as React from 'react';
import { useIntl } from 'react-intl';

import { EExtraFieldType } from '../../../../types/template';

import { TFieldsetRulesetsProps } from './types';
import {
  updateRulesetMessage,
  deleteRuleset,
  addRuleset,
} from './utils';
import { FieldsetRulesList } from './FieldsetRulesList';
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
          <span className={styles['ruleset-card__label']}>
            {formatMessage({ id: 'fieldsets.ruleset-message' })}
          </span>
          <input
            type="text"
            className={styles['ruleset-message-input']}
            value={ruleSet.message || ''}
            placeholder={formatMessage({ id: 'fieldsets.ruleset-message-placeholder' })}
            onChange={(e) =>
              updateRulesetMessage({
                rulesets,
                rulesetApiName: ruleSet.apiName,
                message: e.target.value,
                onRulesetsChange,
              })
            }
            disabled={isReadOnly}
          />

          <FieldsetRulesList
            ruleSet={ruleSet}
            rulesets={rulesets}
            onRulesetsChange={onRulesetsChange}
            isReadOnly={isReadOnly}
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
