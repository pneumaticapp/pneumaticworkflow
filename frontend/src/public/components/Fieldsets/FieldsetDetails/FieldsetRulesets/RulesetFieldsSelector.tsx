import * as React from 'react';

import { useIntl } from 'react-intl';

import { FilterSelect, Tooltip } from '../../../UI';
import { DeleteRoundIcon } from '../../../icons';

import { IExtraField } from '../../../../types/template';
import { IFieldsetRuleSet } from '../../../../types/fieldset';

import {
  getFieldsTooltipText,
  updateRulesetFields,
  removeFieldFromRuleset,
} from './utils';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from './FieldsetRulesets.css';

export type TRulesetFieldsSelectorProps = {
  ruleSet: IFieldsetRuleSet;
  rulesets: IFieldsetRuleSet[];
  fields: IExtraField[];
  numericFields: IExtraField[];
  onRulesetsChange: (rulesets: IFieldsetRuleSet[]) => void;
  isReadOnly?: boolean;
};

export const RulesetFieldsSelector = ({
  ruleSet,
  rulesets,
  fields,
  numericFields,
  onRulesetsChange,
  isReadOnly,
}: TRulesetFieldsSelectorProps) => {
  const { formatMessage } = useIntl();

  const selectedFieldApiNames = new Set(ruleSet.fields || []);
  const selectedFields = numericFields.filter((field) => selectedFieldApiNames.has(field.apiName));

  const tooltipText = getFieldsTooltipText(
    fields.length > 0,
    numericFields.length > 0,
    formatMessage,
  );

  return (
    <>
      <span className={styles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.rule-fields' })}
      </span>
      <Tooltip
        content={tooltipText}
        disabled={numericFields.length > 0 || isReadOnly}
        placement="top-start"
        containerClassName={styles['rule-fields-tooltip-wrapper']}
      >
        <div className={styles['rule-fields-selector']}>
          <FilterSelect<'apiName', 'name', { apiName: string; name: string }>
            isMultiple
            optionIdKey="apiName"
            optionLabelKey="name"
            options={numericFields.map((field) => ({ apiName: field.apiName, name: field.name }))}
            selectedOptions={ruleSet.fields || []}
            placeholderText={formatMessage({ id: 'fieldsets.rule-fields-placeholder' })}
            onChange={(fieldApiNames) =>
              updateRulesetFields({
                rulesets,
                rulesetApiName: ruleSet.apiName,
                fieldApiNames,
                onRulesetsChange,
              })
            }
            resetFilter={() =>
              updateRulesetFields({
                rulesets,
                rulesetApiName: ruleSet.apiName,
                fieldApiNames: [],
                onRulesetsChange,
              })
            }
            isDisabled={isReadOnly || numericFields.length === 0}
            containerClassname={fieldsetDetailsStyles['settings-select']}
            toggleClassName={fieldsetDetailsStyles['settings-select__toggle']}
            menuClassName={fieldsetDetailsStyles['settings-select__menu']}
            renderPlaceholder={() => formatMessage({ id: 'fieldsets.rule-fields-placeholder' })}
          />
        </div>
      </Tooltip>
      
      {selectedFields.length > 0 && (
        <div className={styles['field-tags-list']}>
          {selectedFields.map((field) => (
            <span key={field.apiName} className={styles['field-tag']}>
              <span className={styles['field-tag__name']}>{field.name}</span>
              {!isReadOnly && (
                <button
                  type="button"
                  className={styles['field-tag__close']}
                  aria-label={formatMessage({ id: 'fieldsets.rule-delete' })}
                  onClick={() =>
                    removeFieldFromRuleset({
                      rulesets,
                      rulesetApiName: ruleSet.apiName,
                      fieldApiName: field.apiName,
                      onRulesetsChange,
                    })
                  }
                >
                  <DeleteRoundIcon width={14} height={14} />
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </>
  );
};
