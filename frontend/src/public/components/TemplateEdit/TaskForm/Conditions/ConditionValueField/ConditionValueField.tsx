/* eslint-disable indent */
import React, { useState, ReactNode, ChangeEvent } from 'react';
import { useSelector } from 'react-redux';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { DropdownList } from '../../../../UI/DropdownList';
import { EExtraFieldType, IExtraFieldSelection } from '../../../../../types/template';
import { isArrayWithItems } from '../../../../../utils/helpers';
import { Field } from '../../../../Field';
import { EUserStatus, TUserListItem } from '../../../../../types/user';
import { TTaskVariable } from '../../../types';
import { getUserFullName } from '../../../../../utils/users';
import { EConditionOperators, TConditionRule } from '../types';
import { OPERATORS_WITHOUT_VALUE } from '..';
import { DatePickerCustom } from '../../../../UI/form/DatePicker';
import { toTspDate } from '../../../../../utils/dateTime';
import { getFormattedDropdownOption } from '../utils/getFormattedDropdownOption';
import styles from '../Conditions.css';
import { EStartingType } from '../utils/getDropdownOperators';
import { IApplicationState } from '../../../../../types/redux';

interface IConditionValueFieldProps {
  variable: TTaskVariable | null;
  rule: TConditionRule;
  users: TUserListItem[];
  operator?: EConditionOperators | null;
  isDisabled: boolean;
  changeRuleValue(value: TConditionRule[keyof TConditionRule]): void;
}

export function ConditionValueField({
  variable,
  operator,
  rule,
  users,
  isDisabled,
  changeRuleValue,
}: IConditionValueFieldProps) {
  if (!variable || !operator) return null;
  const groups = useSelector((state: IApplicationState) => state.groups.list);
  const isNoValueOperator = OPERATORS_WITHOUT_VALUE.includes(operator);

  if (isNoValueOperator) return null;

  const { formatMessage } = useIntl();
  const isNumericField = true;

  const renderMap: { [key in EExtraFieldType]: () => ReactNode } & {
    [key in EStartingType]: () => ReactNode;
  } = {
    [EExtraFieldType.Number]: () => renderTextField(isNumericField),
    [EExtraFieldType.String]: renderTextField,
    [EExtraFieldType.Text]: renderTextField,
    [EExtraFieldType.Url]: renderTextField,
    [EExtraFieldType.Checkbox]: renderDropdownField,
    [EExtraFieldType.Radio]: renderDropdownField,
    [EExtraFieldType.Creatable]: renderDropdownField,
    [EExtraFieldType.User]: renderUserField,
    [EExtraFieldType.Date]: renderDateField,
    [EExtraFieldType.File]: () => null,
    [EStartingType.Task]: () => null,
    [EStartingType.Kickoff]: () => null,
  };

  function renderTextField(isNumberType?: boolean) {
    return (
      <Field
        disabled={isDisabled}
        labelClassName={styles['text-field']}
        placeholder={formatMessage({ id: 'templates.conditions.value-placeholder' })}
        value={rule.value!}
        onChange={(e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
          changeRuleValue(e.target.value);
        }}
        {...(isNumberType && { isNumericField, isFromConditionValueField: true })}
      />
    );
  }

  function renderDropdownField() {
    interface IDropdownSelection extends IExtraFieldSelection {
      label: string;
    }

    if (!isArrayWithItems(variable?.selections)) {
      return null;
    }

    const dropdownSelections = variable!.selections.map((selection) => ({ ...selection, label: selection.value }));
    const selectedSelection = dropdownSelections.find((selection) => selection.apiName === rule.value) || null;

    return (
      <DropdownList
        isDisabled={isDisabled}
        isSearchable={false}
        placeholder={formatMessage({ id: 'templates.conditions.value-placeholder' })}
        value={selectedSelection}
        onChange={(option: IDropdownSelection) => {
          changeRuleValue(option.apiName);
        }}
        isClearable={false}
        options={dropdownSelections}
        formatOptionLabel={(option: IDropdownSelection, { context }) =>
          context === 'menu'
            ? getFormattedDropdownOption({
                label: option.label,
                isSelected: option.apiName === rule.value,
                isTooltip: true,
              })
            : option.label
        }
        classNames={{ menu: () => styles['condition__value-field-select-menu'] }}
      />
    );
  }

  function renderUserField() {
    interface IDropdownUser extends TUserListItem {
      label: string;
    }

    const activeUsers = users.filter((user) => user.status === EUserStatus.Active);
    const labelUsers = activeUsers.map((user) => ({ ...user, label: getUserFullName(user) }));
    const labelGroups = groups.map((group) => ({ ...group, label: group.name }));
    const dropdownEntities = [...labelGroups, ...labelUsers];
    const selectedEntity = dropdownEntities.find((user) => user.id === Number(rule.value)) || null;

    return (
      <DropdownList
        isDisabled={isDisabled}
        isSearchable={false}
        placeholder={formatMessage({ id: 'templates.conditions.value-placeholder' })}
        value={selectedEntity}
        onChange={(option: IDropdownUser) => {
          changeRuleValue(option.id);
        }}
        isClearable={false}
        options={dropdownEntities}
        formatOptionLabel={(option: IDropdownUser, { context }) =>
          context === 'menu'
            ? getFormattedDropdownOption({
                label: option.label,
                isSelected: option.id === rule.value,
                isTooltip: true,
              })
            : option.label
        }
        classNames={{ menu: () => styles['condition__value-field-select-menu'] }}
      />
    );
  }

  function renderDateField() {
    const [selectedDate, setSelectedDate] = useState<number | null>(rule.value as number);

    const handleChangeDate = (date: Date) => {
      if (!date) {
        changeRuleValue('');
        setSelectedDate(null);

        return;
      }

      const unixTime = toTspDate(date);

      changeRuleValue(unixTime);
      setSelectedDate(unixTime);
    };

    return (
      <DatePickerCustom
        disabled={isDisabled}
        onChange={handleChangeDate}
        placeholderText={formatMessage({ id: 'templates.conditions.value-placeholder' })}
        selected={selectedDate ? new Date(selectedDate * 1000) : null}
        showPopperArrow={false}
      />
    );
  }

  const conditionValueField = renderMap[variable.type]();

  if (!conditionValueField) return null;

  return (
    <div className={classnames(styles['condition-rule__setting'], styles['condition-rule__value'])}>
      {conditionValueField}
    </div>
  );
}
