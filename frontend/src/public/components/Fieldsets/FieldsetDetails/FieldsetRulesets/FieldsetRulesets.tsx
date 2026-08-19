import * as React from 'react';
import { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { FilterSelect } from '../../../UI';

import { EFieldsetNumberRulesetOperator } from '../../../../types/fieldset';

import {
  FIELDSET_RULE_TYPES,
  FIELDSET_RULE_VALUE_PLACEHOLDER_BY_TYPE,
} from '../../constants';

import { TRulePath, TFieldsetRulesetsProps } from './types';
import {
  updateRuleset,
  deleteGroupAnd,
  getNormalizedRulesetOrders,
  createEmptyRuleset,
  updateRulesetFields,
} from './utils';

import styles from '../FieldsetDetails.css';

export const FieldsetRulesets = ({
  rulesets,
  fields,
  onRulesetsChange,
  isReadOnly,
}: TFieldsetRulesetsProps) => {
  const { formatMessage } = useIntl();

  const ruleTypeOptions = useMemo(
    () =>
      FIELDSET_RULE_TYPES.map((ruleType) => ({
        id: ruleType.value,
        name: formatMessage({ id: ruleType.labelKey }),
      })),
    [formatMessage],
  );

  const getRuleValuePlaceholder = (ruleType: EFieldsetNumberRulesetOperator) =>
    formatMessage({ id: FIELDSET_RULE_VALUE_PLACEHOLDER_BY_TYPE[ruleType] });

  return (
    <div className={styles['list']}>
      <h2 className={styles['section-title']}>
        {formatMessage({ id: 'fieldsets.rules-section' })}
        {isReadOnly && (
          <span className={styles['readonly-badge']}>
            {formatMessage({ id: 'fieldsets.readonly-badge' })}
          </span>
        )}
      </h2>

      {rulesets.length === 0 && (
        <p className={styles['empty-text']}>{formatMessage({ id: 'fieldsets.no-rules' })}</p>
      )}

      {rulesets.map((ruleSet) => (
        <div key={ruleSet.apiName} className={styles['rule-row']}>
          {ruleSet.groupsOr.map((groupOr) =>
            groupOr.groupsAnd.map((groupAndRule) => {
              const rulePath: TRulePath = {
                rulesetApiName: ruleSet.apiName,
                ruleGroupOrApiName: groupOr.apiName,
                ruleGroupAndApiName: groupAndRule.apiName,
              };

              return (
                <React.Fragment key={groupAndRule.apiName}>
                  <FilterSelect<'id', 'name', { id: EFieldsetNumberRulesetOperator; name: string }>
                    optionIdKey="id"
                    optionLabelKey="name"
                    options={ruleTypeOptions}
                    selectedOption={groupAndRule.operator}
                    onChange={(key) => {
                      if (key && key !== groupAndRule.operator) {
                        onRulesetsChange(
                          updateRuleset(rulesets, rulePath, {
                            operator: key as EFieldsetNumberRulesetOperator,
                          }),
                        );
                      }
                    }}
                    resetFilter={() => {}}
                    placeholderText=""
                    isDisabled={isReadOnly}
                    containerClassname={styles['settings-select']}
                    toggleClassName={styles['settings-select__toggle']}
                    menuClassName={styles['settings-select__menu']}
                    renderPlaceholder={() =>
                      ruleTypeOptions.find((option) => option.id === groupAndRule.operator)?.name || ''
                    }
                  />

                  <input
                    type="text"
                    className={styles['rule-value-input']}
                    value={groupAndRule.value}
                    placeholder={getRuleValuePlaceholder(groupAndRule.operator)}
                    onChange={(e) =>
                      onRulesetsChange(
                        updateRuleset(rulesets, rulePath, { value: e.target.value }),
                      )
                    }
                    disabled={isReadOnly}
                  />

                  {!isReadOnly && (
                    <button
                      type="button"
                      className={styles['rule-delete-btn']}
                      onClick={() => onRulesetsChange(deleteGroupAnd(rulesets, rulePath))}
                    >
                      {formatMessage({ id: 'fieldsets.rule-delete' })}
                    </button>
                  )}
                </React.Fragment>
              );
            }),
          )}

          <div className={styles['rule-fields-selector']}>
            <span className={styles['rule-fields-label']}>
              {formatMessage({ id: 'fieldsets.rule-fields' })}
            </span>
            <div className={styles['rule-fields-select']}>
              <FilterSelect<'apiName', 'name', { apiName: string; name: string }>
                isMultiple
                optionIdKey="apiName"
                optionLabelKey="name"
                options={fields.map((field) => ({ apiName: field.apiName, name: field.name }))}
                selectedOptions={ruleSet.fields || []}
                placeholderText={formatMessage({ id: 'fieldsets.rule-fields-placeholder' })}
                onChange={(fieldApiNames) =>
                  onRulesetsChange(updateRulesetFields(rulesets, ruleSet.apiName, fieldApiNames))
                }
                resetFilter={() =>
                  onRulesetsChange(updateRulesetFields(rulesets, ruleSet.apiName, []))
                }
                isDisabled={isReadOnly}
                renderPlaceholder={(opts) => {
                  const selected = (ruleSet.fields || []).length;
                  if (selected === 0)
                    return formatMessage({ id: 'fieldsets.rule-fields-placeholder' });
                  const selectedNames = opts
                    .filter((option) => (ruleSet.fields || []).includes(option.apiName))
                    .map((option) => option.name);
                  return selectedNames.join(', ');
                }}
              />
            </div>
          </div>
        </div>
      ))}

      {!isReadOnly && (
        <button
          type="button"
          className={styles['add-rule-btn']}
          onClick={() =>
            onRulesetsChange(getNormalizedRulesetOrders([...rulesets, createEmptyRuleset()]))
          }
        >
          + {formatMessage({ id: 'fieldsets.add-rule' })}
        </button>
      )}
    </div>
  );
};
