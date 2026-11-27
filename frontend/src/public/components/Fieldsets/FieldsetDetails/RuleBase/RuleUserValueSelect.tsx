import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { EFieldRuleValueType } from '../../../../types/fieldset';
import { FilterSelect, UserSelectOption } from '../../../UI';
import { getUsers } from '../../../../redux/selectors/user';
import { getRegularGroupsList } from '../../../../redux/selectors/groups';
import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';
import type { IRuleUserValueSelectProps, TBuildUserDropdownOptionParams, TUserRuleDropdownOption } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesetsList/FieldsetRulesets.css';

const buildUserDropdownOption = ({
  id,
  displayName,
  valueType,
  avatarUser,
}: TBuildUserDropdownOptionParams): TUserRuleDropdownOption => ({
  apiName: `${valueType}-${id}`,
  name: <UserSelectOption user={avatarUser} name={displayName} />,
  searchByText: displayName,
  rawValue: String(id),
  valueType,
});

export const RuleUserValueSelect = ({ value, valueType, isReadOnly, onChange }: IRuleUserValueSelectProps) => {
  const { formatMessage } = useIntl();
  const users = useSelector(getUsers);
  const groups = useSelector(getRegularGroupsList);

  const dropdownOptions = useMemo<TUserRuleDropdownOption[]>(() => {
    const groupOptions = groups.map((group) =>
      buildUserDropdownOption({
        id: group.id,
        displayName: group.name,
        valueType: EFieldRuleValueType.Group,
        avatarUser: { type: EFieldRuleValueType.Group },
      }),
    );
    const userOptions = getNotDeletedUsers(users || []).map((user) =>
      buildUserDropdownOption({
        id: user.id,
        displayName: getUserFullName(user),
        valueType: EFieldRuleValueType.User,
        avatarUser: user,
      }),
    );
    return [...groupOptions, ...userOptions];
  }, [groups, users]);

  const resolvedValueType = valueType || EFieldRuleValueType.User;
  const selectedOption = dropdownOptions.find(
    (option) => option.rawValue === value && option.valueType === resolvedValueType,
  );
  const selectedLabel = selectedOption?.searchByText || '';
  const placeholderText = formatMessage({ id: 'templates.conditions.value-placeholder' });

  return (
    <div className={styles['rule-value-select']}>
      <FilterSelect<'apiName', 'name', TUserRuleDropdownOption>
        optionIdKey="apiName"
        optionLabelKey="name"
        options={dropdownOptions}
        selectedOption={selectedOption?.apiName || ''}
        isSearchShown
        searchPlaceholder={formatMessage({ id: 'nav.search' })}
        onChange={(key) => {
          if (!key) return;
          const pickedOption = dropdownOptions.find((option) => option.apiName === String(key));
          if (!pickedOption) return;
          onChange(pickedOption.rawValue, pickedOption.valueType);
        }}
        resetFilter={() => {}}
        placeholderText={placeholderText}
        isDisabled={isReadOnly}
        containerClassname={classnames(
          fieldsetDetailsStyles['rule-operator-select'],
          styles['rule-value-select-inner'],
        )}
        toggleClassName={fieldsetDetailsStyles['rule-operator-select__toggle']}
        menuClassName={fieldsetDetailsStyles['rule-operator-select__menu']}
        renderPlaceholder={() =>
          selectedLabel || <span className={styles['rule-select-placeholder']}>{placeholderText}</span>
        }
      />
    </div>
  );
};
