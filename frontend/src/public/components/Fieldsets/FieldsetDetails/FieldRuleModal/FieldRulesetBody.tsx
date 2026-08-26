import * as React from 'react';
import { useIntl } from 'react-intl';

import { FilterSelect } from '../../../UI';
import { FIELD_RULE_VALIDATOR_OPERATOR_OPTIONS } from '../../constants';
import { EFieldRuleType } from '../../../../types/fieldset';
import { RuleList, RulesetMessageInput } from '../RuleBase';
import { addRule, deleteRule, regroupRules, updateRule } from '../RuleBase/utils';
import { createEmptyFieldRule } from './utils';
import { IFieldRulesetBodyProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import rulesetStyles from '../FieldsetRulesets/FieldsetRulesets.css';

export function FieldRulesetBody({ localRuleSet, onUpdateRuleSet }: IFieldRulesetBodyProps) {
  const { formatMessage } = useIntl();

  const { type, message } = localRuleSet;

  const typeOptions = [
    { apiName: EFieldRuleType.Show, name: formatMessage({ id: 'fieldsets.field-rule-modal.type-show' }) },
    { apiName: EFieldRuleType.Validator, name: formatMessage({ id: 'fieldsets.field-rule-modal.type-validator' }) },
  ];
  const selectedTypeLabel = typeOptions.find((option) => option.apiName === type)?.name || '';

  return (
    <>
      <span className={rulesetStyles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.field-rule-modal.type-label' })}
      </span>
      <FilterSelect<'apiName', 'name', { apiName: EFieldRuleType; name: string }>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={typeOptions}
        selectedOption={type}
        onChange={(key) => {
          if (key && key !== type) {
            onUpdateRuleSet({ type: key as EFieldRuleType });
          }
        }}
        resetFilter={() => {}}
        placeholderText=""
        containerClassname={fieldsetDetailsStyles['settings-select']}
        toggleClassName={fieldsetDetailsStyles['settings-select__toggle']}
        menuClassName={fieldsetDetailsStyles['settings-select__menu']}
        renderPlaceholder={() => selectedTypeLabel}
      />
      {type === EFieldRuleType.Validator && (
        <>
          <RulesetMessageInput
            message={message}
            onChange={(msg) => onUpdateRuleSet({ message: msg })}
          />
          <RuleList
            ruleSet={localRuleSet}
            operatorOptions={FIELD_RULE_VALIDATOR_OPERATOR_OPTIONS}
            addRule={() => onUpdateRuleSet(addRule(localRuleSet, createEmptyFieldRule))}
            updateRule={({ ruleGroupOrApiName, ruleGroupAndApiName, ruleChanges }) =>
              onUpdateRuleSet(updateRule(localRuleSet, ruleGroupOrApiName, ruleGroupAndApiName, ruleChanges))
            }
            deleteRule={({ ruleGroupOrApiName, ruleGroupAndApiName }) =>
              onUpdateRuleSet(deleteRule(localRuleSet, ruleGroupOrApiName, ruleGroupAndApiName))
            }
            regroupRules={({ groupOrApiName, groupAndApiName, ruleCombinator }) =>
              onUpdateRuleSet(regroupRules(localRuleSet, groupOrApiName, groupAndApiName, ruleCombinator))
            }
          />
        </>
      )}
    </>
  );
}


