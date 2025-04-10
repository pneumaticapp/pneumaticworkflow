/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';

import { getFieldValidator } from '../utils/getFieldValidator';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { EExtraFieldMode } from '../../../../types/template';
import { DateIcon } from '../../../icons';
import { FieldWithName } from '../utils/FieldWithName';
import { IWorkflowExtraFieldProps } from '..';
import { DatePickerCustom } from '../../../UI/form/DatePicker';
import { toDate, toTspDate } from '../../../../utils/dateTime';

import fieldStyles from './ExtraFieldDate.css';
import styles from '../../KickoffRedux/KickoffRedux.css';



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
  const [selectedDate, setSelectedDate] = React.useState<Date | null>(toDate(value as number | string | null));

  const handleChangeDate = (date: Date) => {
    if (!date) {
      editField({ value: '' });
      setSelectedDate(null);
      return;
    }

    editField({ value: toTspDate(date) });
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
          <DatePickerCustom
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
