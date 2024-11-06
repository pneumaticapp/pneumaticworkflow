/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { format, parse } from 'date-fns';

import { getFieldValidator } from '../utils/getFieldValidator';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { EExtraFieldMode } from '../../../../types/template';
import { DateIcon } from '../../../icons';
import { FieldWithName } from '../utils/FieldWithName';

import { IWorkflowExtraFieldProps } from '..';

import fieldStyles from './ExtraFieldDate.css';
import { DatePicker } from '../../../UI/form/DatePicker/container';
import styles from '../../KickoffRedux/KickoffRedux.css';

const DATE_STRING_TEMPLATE = 'MM/dd/yyyy';

const getStringFromDate = (date: Date) => format(date, DATE_STRING_TEMPLATE);
const getDateFromString = (dateStr: string | null) => {
  if (!dateStr) return null;

  return parse(dateStr, DATE_STRING_TEMPLATE, new Date());
};

export function ExtraFieldDate({
  field,
  field: { value, name, isRequired },
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
}: IWorkflowExtraFieldProps) {
  const handleChangeName = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      editField({ name: e.target.value });
    },
    [editField],
  );

  const handleChangeDescription = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      editField({ description: e.target.value });
    },
    [editField],
  );

  const [selectedDate, setSelectedDate] = React.useState<Date | null>(getDateFromString(value as string | null));
  const handleChangeDate = (date: Date) => {
    if (!date) {
      editField({ value: '' });
      setSelectedDate(null);

      return;
    }

    const strDate = getStringFromDate(date);
    editField({ value: strDate });
    setSelectedDate(date);
  };

  const renderProcessRunField = () => {
    const fieldNameClassName = classnames(getInputNameBackground(labelBackgroundColor), styles['kick-off-input__name']);

    return (
      <div
        className={classnames(fieldStyles['run-container'], styles['kick-off-input__field'])}
        data-autofocus-first-field
      >
        <div className={fieldNameClassName}>
          <div className={classnames(styles['kick-off-input__name-text'], 'extra-field-name')}>{name}</div>
          {isRequired && <span className={styles['kick-off-required-sign']} />}
        </div>
        <div className={fieldStyles['date-input-wrapper']}>
          <DatePicker
            onChange={handleChangeDate}
            placeholderText={descriptionPlaceholder}
            selected={selectedDate}
            showPopperArrow={false}
          />
          <div className={fieldStyles['icon']}>
            <DateIcon />
          </div>
        </div>
      </div>
    );
  };

  const renderField = () => {
    const fieldsMap: { [key in EExtraFieldMode]: React.ReactNode } = {
      [EExtraFieldMode.Kickoff]: (
        <FieldWithName
          field={field}
          descriptionPlaceholder={descriptionPlaceholder}
          namePlaceholder={namePlaceholder}
          mode={mode}
          handleChangeName={handleChangeName}
          labelBackgroundColor={labelBackgroundColor}
          handleChangeDescription={handleChangeDescription}
          validate={getFieldValidator(field, mode)}
          icon={<DateIcon />}
          isDisabled={isDisabled}
          innerRef={innerRef}
        />
      ),
      [EExtraFieldMode.ProcessRun]: renderProcessRunField(),
    };

    return fieldsMap[mode];
  };

  return renderField();
}
