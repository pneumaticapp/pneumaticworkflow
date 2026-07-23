import React, { useRef, useState } from 'react';
import AutosizeInput from 'react-input-autosize';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EFieldLabelPosition } from '../../../../types/fieldset';
import { validateKickoffFieldName } from '../../../../utils/validators';
import { IntlMessages } from '../../../IntlMessages';
import { PencilSmallIcon } from '../../../icons';
import { Button } from '../../../UI/Buttons/Button';
import { FieldLabel } from '../utils/FieldLabel';
import kickoffStyles from '../../KickoffRedux/KickoffRedux.css';
import { EExtraFieldMode } from '../../../../types/template';
import { IExtraFieldFileTemplateProps } from './types';

import styles from './ExtraFieldFile.css';

export function ExtraFieldFileTemplate({
  field,
  isDisabled,
  namePlaceholder,
  labelPosition,
  editField,
}: IExtraFieldFileTemplateProps) {
  const { formatMessage } = useIntl();
  const fieldNameInputRef = useRef<HTMLInputElement | null>(null);
  const [isFocused, setIsFocused] = useState(false);
  const fieldNameErrorMessage = validateKickoffFieldName(field.name) || '';

  return (
    <div
      className={classnames(
        styles['extra-field-file__conteiner--template'],
        labelPosition === EFieldLabelPosition.Left && kickoffStyles['kick-off-input__field_label-left'],
      )}
    >
      {labelPosition === EFieldLabelPosition.Left ? (
        <FieldLabel
          name={field.name}
          isRequired={field.isRequired || false}
          isDisabled={isDisabled}
          mode={EExtraFieldMode.Kickoff}
          namePlaceholder={namePlaceholder}
          handleChangeName={(event) => editField({ name: event.target.value })}
        />
      ) : (
      <div className={styles['extra-field-file__input--template']}>
        <AutosizeInput
          inputRef={(ref) => {
            fieldNameInputRef.current = ref;
          }}
          inputClassName={classnames(
            styles['extra-field-file__input-name--template'],
            fieldNameErrorMessage && styles['extra-field-file__input-name-error--template'],
          )}
          onChange={(event) => editField({ name: event.target.value })}
          placeholder={namePlaceholder}
          type="text"
          value={field.name}
          disabled={isDisabled}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              setIsFocused(false);
              event.currentTarget.blur();
            }
          }}
        />
        {field.isRequired && <span className={kickoffStyles['kick-off-required-sign']} />}
        {!isFocused && (
          <button
            type="button"
            aria-label={namePlaceholder}
            onClick={() => fieldNameInputRef.current?.focus()}
            className={classnames(
              kickoffStyles['kick-off-edit-name'],
              styles['extra-field-file__edit-name-button--template'],
            )}
          >
            <PencilSmallIcon />
          </button>
        )}
      </div>
      )}
      {fieldNameErrorMessage && (
        <p className={styles['extra-field-file__error-message--template']}>
          <IntlMessages id={fieldNameErrorMessage} />
        </p>
      )}
      <div className={styles['extra-field-file__upload-button-conteiner']}>
        <Button
          label={formatMessage({ id: 'file-upload.label-upload-button' })}
          size="sm"
          buttonStyle="transparent-black"
          disabled
          className={styles['extra-field-file__upload-button--template']}
        />
      </div>
    </div>
  );
}
