import classnames from 'classnames';
import * as React from 'react';
import { ChangeEvent, useCallback, useMemo, useRef, useState } from 'react';
import TextareaAutosize from 'react-textarea-autosize';

import { validateKickoffFieldName } from '../../../../utils/validators';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { getInputNameBackground } from './getInputNameBackground';
import { EExtraFieldMode } from '../../../../types/template';
import { PencilSmallIcon } from '../../../icons';

import styles from '../../KickoffRedux/KickoffRedux.css';

export interface IFieldLabelProps {
  name: string;
  isRequired: boolean;
  isDisabled: boolean;
  mode?: EExtraFieldMode;
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
        fieldNameError && styles['kick-off-input__name_error'],
        className,
      ),
    [labelBackgroundColor, fieldNameError, className],
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
