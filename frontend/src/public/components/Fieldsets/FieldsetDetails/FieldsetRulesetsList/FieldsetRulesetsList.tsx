import * as React from 'react';
import { useIntl } from 'react-intl';

import { EExtraFieldType } from '../../../../types/template';

import { TFieldsetRulesetsListProps } from './types';
import { addRuleset } from './utils';
import { FieldsetRulesetItem } from './FieldsetRulesetItem';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from './FieldsetRulesets.css';

export const FieldsetRulesetsList = ({
  rulesets,
  fields,
  onRulesetsChange,
  isReadOnly,
}: TFieldsetRulesetsListProps) => {
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
        <FieldsetRulesetItem
          key={ruleSet.apiName}
          ruleSet={ruleSet}
          rulesets={rulesets}
          fields={fields}
          numericFields={numericFields}
          onRulesetsChange={onRulesetsChange}
          isReadOnly={isReadOnly}
        />
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
