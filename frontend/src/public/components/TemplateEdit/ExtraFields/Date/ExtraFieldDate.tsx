/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';

import { getFieldValidator } from '../utils/getFieldValidator';
import { getInputNameBackground } from '../utils/getInputNameBackground';
import { EExtraFieldMode } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { DateIcon } from '../../../icons';
import { FieldWithName } from '../utils/FieldWithName';
import { FieldLabel } from '../utils/FieldLabel';
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
  labelPosition,
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
    const isLabelLeft = labelPosition === EFieldLabelPosition.Left;
    const fieldNameClassName = classnames(getInputNameBackground(labelBackgroundColor), styles['kick-off-input__name']);

    return (
      <div
        className={classnames(
          fieldStyles['run-container'],
          styles['kick-off-input__field'],
          isLabelLeft && styles['kick-off-input__field_label-left'],
        )}
        data-autofocus-first-field
      >
        {isLabelLeft ? (
          <FieldLabel
            name={name}
            isRequired={isRequired || false}
            isDisabled={isDisabled}
            mode={mode}
            labelBackgroundColor={labelBackgroundColor}
            handleChangeName={handleChangeName}
            className={styles['kick-off-input__name_label-left_centered']}
          />
        ) : (
          <div className={fieldNameClassName}>
            <div className={classnames(styles['kick-off-input__name-text'], 'extra-field-name')}>{name}</div>
            {isRequired && <span className={styles['kick-off-required-sign']} />}
          </div>
        )}
        <div className={classnames(fieldStyles['date-input-wrapper'], isLabelLeft && fieldStyles['date-input-wrapper_label-left'])}>
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
          labelPosition={labelPosition}
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
