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
  useRef,
  useState,
} from 'react';
import TextareaAutosize from 'react-textarea-autosize';

import { Field, EFieldTagName } from '../../../Field';
import { validateKickoffFieldName } from '../../../../utils/validators';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { getInputNameBackground } from './getInputNameBackground';
import { EExtraFieldMode, IExtraField } from '../../../../types/template';
import { PencilSmallIcon } from '../../../icons';

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
  onClick?(): void;
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
      onNumericKeyDown,
      isNumericField,
    },
    ref,
  ) => {
    const editInputRef = useRef<HTMLTextAreaElement | null>(null);
    const [isFocused, setIsFocused] = useState(false);

    const descriptionInputRef = useCallback(
      (node: HTMLInputElement | null) => {
        assignInputRef(innerRef, node);
        assignInputRef(ref, node);
      },
      [innerRef, ref],
    );

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

    const handleEditNameClick = useCallback(() => {
      editInputRef.current?.focus();
    }, []);

    const handleNameTextareaRef = useCallback((element: HTMLTextAreaElement | null) => {
      editInputRef.current = element;
    }, []);

    const handleNameFocus = useCallback(() => {
      setIsFocused(true);
    }, []);

    const handleNameBlur = useCallback(() => {
      setIsFocused(false);
    }, []);

    const fieldNameError = useMemo(() => validateKickoffFieldName(name), [name]);

    const fieldNameClassName = useMemo(
      () =>
        classnames(
          getInputNameBackground(labelBackgroundColor),
          styles['kick-off-input__name'],
          fieldNameError && styles['kick-off-input__name_error'],
        ),
      [labelBackgroundColor, fieldNameError],
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

    return (
      <div className={styles['kick-off-input__field']} data-autofocus-first-field>
        <div className={fieldNameClassName}>
          <TextareaAutosize
            disabled={mode !== EExtraFieldMode.Kickoff || isDisabled}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            value={name}
            ref={handleNameTextareaRef}
            onFocus={handleNameFocus}
            onBlur={handleNameBlur}
            minRows={1}
            className={styles['kick-off-input__name-textarea']}
          />
          {isRequired && <span className={styles['kick-off-required-sign']} />}
          {!isFocused && mode === EExtraFieldMode.Kickoff && (
            <button
              type="button"
              aria-label="Edit field name"
              onClick={handleEditNameClick}
              className={styles['kick-off-edit-name']}
            >
              <PencilSmallIcon />
            </button>
          )}
        </div>
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
            onKeyDown={onNumericKeyDown}
            isNumericField={isNumericField}
          />
        </div>
      </div>
    );
  },
);
FieldWithName.displayName = 'FieldWithName';

