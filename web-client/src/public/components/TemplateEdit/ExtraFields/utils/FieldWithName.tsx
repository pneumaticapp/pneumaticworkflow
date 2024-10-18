/* eslint-disable */
/* prettier-ignore */
import * as classnames from 'classnames';
import * as React from 'react';

import { Field, EFieldTagName } from '../../../Field';
import { validateKickoffFieldName } from '../../../../utils/validators';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { getInputNameBackground } from './getInputNameBackground';
import { EExtraFieldMode, IExtraField } from '../../../../types/template';
import { PencilSmallIcon } from '../../../icons';

import AutosizeInput from 'react-input-autosize';

import styles from '../../KickoffRedux/KickoffRedux.css';

interface IKickoffFormFieldWithNameProps {
  field: IExtraField;
  inputClassName?: string;
  icon?: React.ReactNode;
  mode?: EExtraFieldMode;
  labelBackgroundColor?: EInputNameBackgroundColor;
  tagName?: EFieldTagName;
  namePlaceholder?: string;
  descriptionPlaceholder?: string;
  shouldReplaceWithLabel?: boolean;
  isDisabled: boolean;
  innerRef?: React.Ref<HTMLInputElement>;
  accountId?: number;
  handleChangeName(e: React.ChangeEvent<HTMLInputElement>): void;
  handleChangeDescription(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void;
  validate(value: string): string;
  onClick?(): void;
}

export const FieldWithName = React.forwardRef(
  (
    {
      field: { description = '', isRequired = false, name, value },
      inputClassName,
      icon,
      descriptionPlaceholder,
      namePlaceholder,
      mode,
      tagName,
      handleChangeName,
      handleChangeDescription,
      validate,
      onClick,
      shouldReplaceWithLabel = false,
      isDisabled,
      labelBackgroundColor,
      innerRef,
      accountId,
    }: IKickoffFormFieldWithNameProps,
    ref,
  ) => {
    const editInputRef = React.useRef<HTMLInputElement | null>(null);
    const [isFocused, setIsFocused] = React.useState(false);

    const getFieldNameError = () => {
      return validateKickoffFieldName(name);
    };

    const fieldNameClassName = classnames(
      getInputNameBackground(labelBackgroundColor),
      styles['kick-off-input__name'],
      getFieldNameError() && styles['kick-off-input__name_error'],
    );

    const labelReplacementClassName = classnames(shouldReplaceWithLabel && styles['label-replacement-class-name']);

    return (
      <div className={styles['kick-off-input__field']} data-autofocus-first-field={true}>
        <div className={fieldNameClassName}>
          <AutosizeInput
            disabled={mode !== EExtraFieldMode.Kickoff || isDisabled}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            type="text"
            value={name}
            inputRef={(ref) => (editInputRef.current = ref)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                setIsFocused(false);
                event.currentTarget.blur();
              }
            }}
          />
          {isRequired && <span className={styles['kick-off-required-sign']} />}
          {!isFocused && mode === EExtraFieldMode.Kickoff && (
            <button onClick={() => editInputRef.current?.focus()} className={styles['kick-off-edit-name']}>
              <PencilSmallIcon />
            </button>
          )}
        </div>
        <div className={styles['kick-off-input__description']} onClick={onClick}>
          <Field
            labelClassName="w-100"
            onChange={handleChangeDescription}
            placeholder={descriptionPlaceholder}
            validate={validate}
            value={mode === EExtraFieldMode.Kickoff ? description : (value as string)}
            className={classnames(inputClassName, styles['kickoff-input_single-line'])}
            icon={icon}
            tagName={tagName}
            disabled={isDisabled}
            shouldReplaceWithLabel={shouldReplaceWithLabel}
            labelReplacementClassName={labelReplacementClassName}
            labelReplacementValue={descriptionPlaceholder}
            errorMessage={getFieldNameError()}
            innerRef={innerRef}
            accountId={accountId}
          />
        </div>
      </div>
    );
  },
);
