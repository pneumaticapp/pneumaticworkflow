import * as React from 'react';

import { getFieldValidator } from '../utils/getFieldValidator';
import { EExtraFieldMode } from '../../../../types/template';
import { EFieldTagName } from '../../../Field';
import { FieldWithName } from '../utils/FieldWithName';

import { IWorkflowExtraFieldProps } from '..';

export const ExtraFieldText = ({
  field,
  intl,
  descriptionPlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }),
  namePlaceholder = intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }),
  mode = EExtraFieldMode.Kickoff,
  editField,
  isDisabled = false,
  labelBackgroundColor,
  innerRef,
  accountId,
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

  return (
    <FieldWithName
      ref={innerRef}
      field={field}
      descriptionPlaceholder={descriptionPlaceholder}
      namePlaceholder={namePlaceholder}
      mode={mode}
      labelBackgroundColor={labelBackgroundColor}
      tagName={mode === EExtraFieldMode.ProcessRun ? EFieldTagName.RichText : EFieldTagName.Textarea}
      handleChangeName={handleChangeName}
      handleChangeDescription={handleChangeDescription}
      validate={getFieldValidator(field, mode)}
      isDisabled={isDisabled}
      accountId={accountId}
    />
  );
};
