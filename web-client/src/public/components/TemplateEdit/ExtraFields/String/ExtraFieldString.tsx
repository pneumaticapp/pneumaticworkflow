/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { getFieldValidator } from '../utils/getFieldValidator';
import { EExtraFieldMode } from '../../../../types/template';
import { FieldWithName } from '../utils/FieldWithName';

import { IWorkflowExtraFieldProps } from '..';

import fieldStyles from './ExtraFieldString.css';

export const ExtraFieldString = ({
  field,
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
}: IWorkflowExtraFieldProps) => {
  const handleChangeName = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      editField({ name: e.target.value });
    },
    [editField],
  );

  const handleChangeDescription = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      if (mode === EExtraFieldMode.Kickoff) {
        editField({ description: e.target.value });
      } else {
        editField({ value: e.target.value });
      }
    },
    [editField],
  );

  const renderField = () => {
    const baseField = (
      <FieldWithName
        field={field}
        descriptionPlaceholder={descriptionPlaceholder}
        namePlaceholder={namePlaceholder}
        mode={mode}
        labelBackgroundColor={labelBackgroundColor}
        handleChangeName={handleChangeName}
        handleChangeDescription={handleChangeDescription}
        validate={getFieldValidator(field, mode)}
        isDisabled={isDisabled}
        innerRef={innerRef}
      />
    );

    const fieldsMap: { [key in EExtraFieldMode]: React.ReactNode } = {
      [EExtraFieldMode.Kickoff]: baseField,
      [EExtraFieldMode.ProcessRun]: <div className={fieldStyles['run-container']}>{baseField}</div>,
    };

    return fieldsMap[mode];
  };

  return <>{renderField()}</>;
};
