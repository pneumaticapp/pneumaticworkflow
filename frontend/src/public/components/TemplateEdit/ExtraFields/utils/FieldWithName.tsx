import classnames from 'classnames';
import React, {
  ChangeEvent,
  forwardRef,
  KeyboardEvent,
  MutableRefObject,
  ReactNode,
  Ref,
  useCallback,
  useMemo,
} from 'react';

import { Field, EFieldTagName } from '../../../Field';
import { validateKickoffFieldName } from '../../../../utils/validators';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { EExtraFieldMode, IExtraField } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { FieldLabel } from './FieldLabel';

import styles from '../../KickoffRedux/KickoffRedux.css';

interface IKickoffFormFieldWithNameProps {
  field: IExtraField;
  inputClassName?: string;
  icon?: ReactNode;
  mode?: EExtraFieldMode;
  labelBackgroundColor?: EInputNameBackgroundColor;
  tagName?: EFieldTagName;
  namePlaceholder?: string;
  descriptionPlaceholder?: string;
  shouldReplaceWithLabel?: boolean;
  isDisabled: boolean;
  innerRef?: Ref<HTMLInputElement>;
  accountId?: number;
  handleChangeName(e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void;
  handleChangeDescription(e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void;
  validate(value: string): string;
  labelPosition: EFieldLabelPosition;
  labelClassName?: string;
  onClick?(): void;
  editorClassName?: string;
  onNumericKeyDown?(event: KeyboardEvent<HTMLInputElement>): void;
  isNumericField?: boolean;
}

const assignInputRef = (
  targetRef: Ref<HTMLInputElement> | undefined,
  node: HTMLInputElement | null,
): void => {
  if (!targetRef) {
    return;
  }
  if (typeof targetRef === 'function') {
    targetRef(node);
    return;
  }
  (targetRef as MutableRefObject<HTMLInputElement | null>).current = node;
};

export const FieldWithName = forwardRef<HTMLInputElement, IKickoffFormFieldWithNameProps>(
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
      labelPosition,
      labelClassName,
      onNumericKeyDown,
      isNumericField,
      editorClassName,
    },
    ref,
  ) => {
    const descriptionInputRef = useCallback(
      (node: HTMLInputElement | null) => {
        assignInputRef(innerRef, node);
        assignInputRef(ref, node);
      },
      [innerRef, ref],
    );

    const fieldNameError = useMemo(() => validateKickoffFieldName(name), [name]);

    const handleDescriptionWrapperKeyDown = useCallback(
      (event: KeyboardEvent<HTMLDivElement>) => {
        if (!onClick) {
          return;
        }
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onClick();
        }
      },
      [onClick],
    );

    const labelReplacementClassName = useMemo(
      () => classnames(shouldReplaceWithLabel && styles['label-replacement-class-name']),
      [shouldReplaceWithLabel],
    );

    const descriptionFieldValue = useMemo(
      () => (mode === EExtraFieldMode.Kickoff ? description : (value as string)),
      [mode, description, value],
    );

    const descriptionInteractiveProps = useMemo(
      () =>
        onClick
          ? {
            onClick,
            onKeyDown: handleDescriptionWrapperKeyDown,
            role: 'button' as const,
            tabIndex: 0,
            'aria-label': 'Field description',
          }
          : {},
      [onClick, handleDescriptionWrapperKeyDown],
    );

    const fieldContainerClassName = classnames(
      styles['kick-off-input__field'],
      labelPosition === EFieldLabelPosition.Left && styles['kick-off-input__field_label-left'],
    );

    return (
      <div className={fieldContainerClassName} data-autofocus-first-field>
        <FieldLabel
          name={name}
          isRequired={isRequired}
          isDisabled={isDisabled}
          mode={mode}
          labelBackgroundColor={labelBackgroundColor}
          namePlaceholder={namePlaceholder}
          handleChangeName={handleChangeName}
          {...(labelClassName && { className: labelClassName })}
        />
        <div className={styles['kick-off-input__description']} {...descriptionInteractiveProps}>
          <Field
            labelClassName="w-100"
            onChange={handleChangeDescription}
            placeholder={descriptionPlaceholder}
            validate={validate}
            value={descriptionFieldValue}
            className={classnames(inputClassName, styles['kickoff-input_single-line'])}
            icon={icon}
            tagName={tagName}
            disabled={isDisabled}
            shouldReplaceWithLabel={shouldReplaceWithLabel}
            labelReplacementClassName={labelReplacementClassName}
            labelReplacementValue={descriptionPlaceholder}
            errorMessage={fieldNameError}
            innerRef={descriptionInputRef}
            accountId={accountId}
            editorClassName={editorClassName}
            onKeyDown={onNumericKeyDown}
            isNumericField={isNumericField}
          />
        </div>
      </div>
    );
  },
);
FieldWithName.displayName = 'FieldWithName';

