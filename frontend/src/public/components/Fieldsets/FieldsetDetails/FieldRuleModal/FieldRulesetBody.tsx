import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { FilterSelect, Tooltip } from '../../../UI';
import { FIELD_RULE_VALIDATOR_OPERATOR_OPTIONS } from '../../constants';
import { EFieldRuleType } from '../../../../types/fieldset';
import { RuleList, RulesetMessageInput } from '../RuleBase';
import { addRule, deleteRule, regroupRules, updateRule } from '../RuleBase/utils';
import { createEmptyFieldRule, createEmptyFieldRuleGroupOr } from './utils';
import { IFieldRulesetBodyProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import rulesetStyles from '../FieldsetRulesets/FieldsetRulesets.css';

export function FieldRulesetBody({
  localRuleSet,
  rulesFieldOptions,
  onUpdateRuleSet,
}: IFieldRulesetBodyProps) {
  const { formatMessage } = useIntl();
  const [isTouchedName, setIsTouchedName] = useState(false);

  const { type, message, name } = localRuleSet;

  useEffect(() => {
    setIsTouchedName(false);
  }, [type]);

  const isNoOtherFields = (rulesFieldOptions?.length ?? 0) === 0;

  const typeOptions: Array<{
    apiName: EFieldRuleType;
    name: React.ReactNode;
    customClickHandler?: () => void;
  }> = [
    {
      apiName: EFieldRuleType.Validator,
      name: formatMessage({ id: 'fieldsets.field-rule-modal.type-validator' }),
    },
    {
      apiName: EFieldRuleType.Show,
      name: isNoOtherFields ? (
        <Tooltip
          interactive={false}
          contentClassName={rulesetStyles['rule-field-tooltip']}
          content={formatMessage({ id: 'fieldsets.field-rule.no-other-fields-tooltip' })}
        >
          <span className={rulesetStyles['rule-option_disabled']}>
            {formatMessage({ id: 'fieldsets.field-rule-modal.type-show' })}
          </span>
        </Tooltip>
      ) : (
        formatMessage({ id: 'fieldsets.field-rule-modal.type-show' })
      ),
      customClickHandler: isNoOtherFields ? () => {} : undefined,
    },
  ];

  const selectedTypeLabel = type === EFieldRuleType.Show
    ? formatMessage({ id: 'fieldsets.field-rule-modal.type-show' })
    : formatMessage({ id: 'fieldsets.field-rule-modal.type-validator' });

  return (
    <>
      <span className={rulesetStyles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.field-rule-modal.name-label' })}
      </span>
      <input
        type="text"
        className={classnames(rulesetStyles['ruleset-message-input'], {
          [rulesetStyles['ruleset-message-input_error']]: isTouchedName && (!name || !name.trim()),
        })}
        value={name || ''}
        placeholder={formatMessage({ id: 'fieldsets.field-rule-modal.name-placeholder' })}
        onChange={(event) => {
          onUpdateRuleSet({ name: event.target.value });
        }}
        onFocus={() => setIsTouchedName(false)}
        onBlur={() => setIsTouchedName(true)}
      />
      <span className={rulesetStyles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.field-rule-modal.type-label' })}
      </span>
      <FilterSelect<'apiName', 'name', { apiName: EFieldRuleType; name: React.ReactNode; customClickHandler?: () => void }>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={typeOptions}
        selectedOption={type}
        onChange={(key) => {
          if (key && key !== type) {
            const newType = key as EFieldRuleType;
            setIsTouchedName(false);
            onUpdateRuleSet({
              type: newType,
              message: newType === EFieldRuleType.Validator ? '' : null,
              groupsOr: [createEmptyFieldRuleGroupOr(newType)],
            });
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
        <RulesetMessageInput
          message={message}
          onChange={(newMessage) => onUpdateRuleSet({ message: newMessage })}
        />
      )}
      <RuleList
        ruleSet={localRuleSet}
        ruleType={type}
        operatorOptions={FIELD_RULE_VALIDATOR_OPERATOR_OPTIONS}
        rulesFieldOptions={rulesFieldOptions}
        addRule={() => onUpdateRuleSet(addRule(localRuleSet, () => createEmptyFieldRule(type)))}
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
  );
}


