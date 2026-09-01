import * as React from 'react';
import { useState, useEffect, useMemo } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector, useDispatch } from 'react-redux';

import { NumericFormat } from 'react-number-format';
import { EExtraFieldType } from '../../../../types/template';
import { FilterSelect } from '../../../UI';
import { DatePickerCustom } from '../../../UI/form/DatePicker';
import { toDate, toTspDate } from '../../../../utils/dateTime';
import { getUsers } from '../../../../redux/selectors/user';
import { getNotDeletedUsers, getUserFullName } from '../../../../utils/users';
import { IFieldRuleValueFieldProps, SELECTION_FIELD_TYPES } from './types';
import { loadDatasetForMap } from '../../../../redux/datasets/slice';
import { getDatasetFromMap } from '../../../../redux/selectors/datasets';
import { IApplicationState } from '../../../../types/redux';

import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';


export const FieldsetFieldRulesValue = ({
  fieldType,
  value,
  selections,
  datasetId,
  isReadOnly,
  onChange,
}: IFieldRuleValueFieldProps) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const users = useSelector(getUsers) || [];

  const isSelectionField = Boolean(fieldType && SELECTION_FIELD_TYPES.includes(fieldType));

  const datasetFromMap = useSelector((state: IApplicationState) =>
    datasetId ? getDatasetFromMap(datasetId)(state) : undefined,
  );

  useEffect(() => {
    if (isSelectionField && datasetId && !datasetFromMap) {
      dispatch(loadDatasetForMap(datasetId));
    }
  }, [isSelectionField, datasetId, datasetFromMap, dispatch]);

  const [isTouched, setIsTouched] = useState(false);

  useEffect(() => {
    setIsTouched(false);
  }, [value, fieldType]);

  const isUserField = fieldType === EExtraFieldType.User;

  const dropdownOptions = useMemo(() => {
    if (!isSelectionField && !isUserField) {
      return [];
    }
    if (isUserField) {
      return getNotDeletedUsers(users).map((user) => ({
        apiName: String(user.id),
        name: getUserFullName(user),
      }));
    }
    if (datasetId) {
      return (datasetFromMap?.items || []).map((item) => ({
        apiName: item.value,
        name: item.value,
      }));
    }
    return (selections || []).map((item) => {
      const optionValue = typeof item === 'string' ? item : item.value;
      return {
        apiName: optionValue,
        name: optionValue,
      };
    });
  }, [isSelectionField, isUserField, users, datasetId, datasetFromMap?.items, selections]);

  if (fieldType === EExtraFieldType.File) {
    return null;
  }

  if (isSelectionField || isUserField) {

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
