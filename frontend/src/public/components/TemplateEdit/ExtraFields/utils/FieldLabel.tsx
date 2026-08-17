import classnames from 'classnames';
import * as React from 'react';
import { ChangeEvent, useCallback, useMemo, useRef, useState } from 'react';
import TextareaAutosize from 'react-textarea-autosize';

import { validateKickoffFieldName } from '../../../../utils/validators';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { getInputNameBackground } from './getInputNameBackground';
import { EExtraFieldMode } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { PencilSmallIcon } from '../../../icons';

import styles from '../../KickoffRedux/KickoffRedux.css';

export interface IFieldLabelProps {
  name: string;
  isRequired: boolean;
  isDisabled: boolean;
  mode?: EExtraFieldMode;
  labelPosition?: EFieldLabelPosition;
  labelBackgroundColor?: EInputNameBackgroundColor;
  namePlaceholder?: string;
  className?: string;
  handleChangeName(e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void;
}

export function FieldLabel({
  name,
  isRequired,
  isDisabled,
  mode,
  labelPosition,
  labelBackgroundColor,
  namePlaceholder,
  className,
  handleChangeName,
}: IFieldLabelProps) {
  const editInputRef = useRef<HTMLTextAreaElement | null>(null);
  const [isFocused, setIsFocused] = useState(false);

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
  const isKickoffEditorMode = mode === EExtraFieldMode.Kickoff;

  const fieldNameClassName = useMemo(
    () =>
      classnames(
        getInputNameBackground(labelBackgroundColor),
        styles['kick-off-input__name'],
        labelPosition === EFieldLabelPosition.Left && styles['kick-off-input__name_label-left_aligned-start'],
        isKickoffEditorMode && styles['kick-off-input__name_kickoff-edit'],
        fieldNameError && styles['kick-off-input__name_error'],
        className,
      ),
    [labelBackgroundColor, labelPosition, fieldNameError, isKickoffEditorMode, className],
  );

  return (
    <div className={fieldNameClassName}>
      {isKickoffEditorMode ? (
        <>
          <TextareaAutosize
            disabled={isDisabled}
            onChange={handleChangeName}
            placeholder={namePlaceholder}
            value={name}
            ref={handleNameTextareaRef}
            onFocus={handleNameFocus}
            onBlur={handleNameBlur}
            minRows={1}
            className={styles['kick-off-input__name-textarea']}
            data-use-input
          />
          {isRequired && <span aria-label="required" className={styles['kick-off-required-sign']} />}
          {!isFocused && (
            <button
              type="button"
              aria-label="Edit field name"
              onClick={handleEditNameClick}
              className={styles['kick-off-edit-name']}
            >
              <PencilSmallIcon />
            </button>
          )}
        </>
      ) : (
        <>
          <div className={styles['kick-off-input__name-readonly']}>{name}</div>
          {isRequired && <span aria-label="required" className={styles['kick-off-required-sign']} />}
        </>
      )}
    </div>
  );
}
