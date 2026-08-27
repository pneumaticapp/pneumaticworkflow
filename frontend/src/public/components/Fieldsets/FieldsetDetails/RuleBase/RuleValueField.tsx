import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { NumericFormat } from 'react-number-format';
import { EExtraFieldType } from '../../../../types/template';
import { FilterSelect } from '../../../UI';
import { DatePickerCustom } from '../../../UI/form/DatePicker';
import { toDate, toTspDate } from '../../../../utils/dateTime';
import { getUsers } from '../../../../redux/selectors/user';
import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';
import { TFieldsetFieldRulesValueProps } from './types';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

const SELECTION_FIELD_TYPES = [
  EExtraFieldType.Checkbox,
  EExtraFieldType.Radio,
  EExtraFieldType.Creatable,
];

export const FieldsetFieldRulesValue = ({
  fieldType,
  value,
  selections,
  isReadOnly,
  onChange,
}: TFieldsetFieldRulesValueProps) => {
  const { formatMessage } = useIntl();
  const users = useSelector(getUsers) || [];

  if (fieldType === EExtraFieldType.File) {
    return null;
  }

  const isSelectionField = Boolean(fieldType && SELECTION_FIELD_TYPES.includes(fieldType));
  const isUserField = fieldType === EExtraFieldType.User;

  if (isSelectionField || isUserField) {
    const dropdownOptions = isUserField
      ? getNotDeletedUsers(users).map((user) => ({
        apiName: String(user.id),
        name: getUserFullName(user),
      }))
      : (selections || []).map((item) => {
        const optionValue = typeof item === 'string' ? item : item.value;
        return {
          apiName: optionValue,
          name: optionValue,
        };
      });

    const selectedOption = dropdownOptions.find((option) => option.apiName === value);
    const selectedLabel = selectedOption?.name || '';
    const placeholderText = formatMessage({ id: 'templates.conditions.value-placeholder' });

    return (
      <div className={styles['rule-value-select']}>
        <FilterSelect<'apiName', 'name', { apiName: string; name: string }>
          optionIdKey="apiName"
          optionLabelKey="name"
          options={dropdownOptions}
          selectedOption={value}
          onChange={(key) => {
            if (key) {
              onChange(String(key));
            }
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
  }

  if (fieldType === EExtraFieldType.Date) {
    const selectedDate = toDate(value);

    const handleDateChange = (date: Date | null) => {
      if (!date) {
        onChange('');
        return;
      }
      const unixTimestamp = toTspDate(date);
      onChange(unixTimestamp ? String(unixTimestamp) : '');
    };

    return (
      <div className={styles['rule-value-select']}>
        <DatePickerCustom
          disabled={isReadOnly}
          onChange={handleDateChange}
          placeholderText={formatMessage({ id: 'templates.conditions.value-placeholder' })}
          selected={selectedDate}
          showPopperArrow={false}
        />
      </div>
    );
  }

  const [isTouched, setIsTouched] = useState(false);

  useEffect(() => {
    setIsTouched(false);
  }, [value, fieldType]);

  const isValueError = isTouched && (!value || !value.trim());

  if (fieldType === EExtraFieldType.Number) {
    const placeholderText = formatMessage({ id: 'fieldsets.rule-value-placeholder-number' });

    return (
      <NumericFormat
        value={value}
        onValueChange={(values) => {
          onChange(values.value);
        }}
        onFocus={() => setIsTouched(false)}
        onBlur={() => setIsTouched(true)}
        allowNegative
        decimalSeparator="."
        thousandSeparator={false}
        allowedDecimalSeparators={['.', ',']}
        disabled={isReadOnly}
        placeholder={placeholderText}
        className={classnames(styles['rule-value-input'], {
          [styles['rule-value-input_error']]: isValueError,
        })}
      />
    );
  }

  const placeholderText = formatMessage({ id: 'templates.conditions.value-placeholder' });

  return (
    <input
      type="text"
      className={classnames(styles['rule-value-input'], {
        [styles['rule-value-input_error']]: isValueError,
      })}
      value={value}
      placeholder={placeholderText}
      onChange={(event) => {
        onChange(event.target.value);
      }}
      onFocus={() => setIsTouched(false)}
      onBlur={() => setIsTouched(true)}
      disabled={isReadOnly}
    />
  );
};
