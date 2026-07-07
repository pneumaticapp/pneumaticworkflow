import React, { useEffect, useState } from 'react';
import TextareaAutosize from 'react-textarea-autosize';
import classnames from 'classnames';

import { EditIcon } from '../../icons';
import { Loader } from '../Loader';

import styles from './EditableText.css';

export interface IEditableTextProps {
  text: string;
  className?: string;
  isLoading?: boolean;
  placeholder?: string;
  onChangeText(value: string): void;
  editButtonHint?: string;
  errorMessage?: string;
  validationAnchor?: string;
}

export function EditableText({
  isLoading,
  text,
  className,
  placeholder,
  editButtonHint,
  onChangeText,
  errorMessage,
  validationAnchor,
}: IEditableTextProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editableText, setEditableText] = useState(text);

  useEffect(() => {
    setEditableText(text);
  }, [text]);

  const startEditState = () => setIsEditing(true);

  if (!isEditing) {
    return (
      <div data-template-validation-anchor={validationAnchor}>
        <div
          className={classnames(className, styles['text'], errorMessage && styles['text_error'])}
          onClick={startEditState}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            startEditState();
          }
        }}
        role="button"
        tabIndex={0}
      >
        {text}
        <span className={styles['edit-button-wrapper']}>
          &#xfeff;
          <span
            role="button"
            aria-label={editButtonHint}
            onClick={startEditState}
            className={styles['edit-button']}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                startEditState();
              }
            }}
            tabIndex={0}
          >
            <EditIcon className={styles['edit-button__icon']} />
          </span>
        </span>
      </div>
        {errorMessage && <p className={styles['error-message']} role="alert">{errorMessage}</p>}
      </div>
    );
  }

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditableText(event.target.value);
    onChangeText(event.target.value);
  };

  const handleBlur = () => {
    const trimmedText = editableText.trim();
    if (trimmedText !== text) {
      onChangeText(trimmedText);
    }
    setIsEditing(false);
  };

  return (
    <form
      className={classnames(className, errorMessage && styles['form_error'])}
      data-template-validation-anchor={validationAnchor}
      onSubmit={(e) => e.preventDefault()}
    >
      <Loader isLoading={isLoading} />
      <TextareaAutosize
        translate={undefined}
        onFocus={(e) => e.currentTarget.setSelectionRange(e.currentTarget.value.length, e.currentTarget.value.length)}
        autoFocus
        value={editableText}
        onBlur={handleBlur}
        onChange={handleChange}
        className={styles['textarea']}
        placeholder={placeholder}
        spellCheck={false}
      />
      {errorMessage && <p className={styles['error-message']} role="alert">{errorMessage}</p>}
    </form>
  );
}
