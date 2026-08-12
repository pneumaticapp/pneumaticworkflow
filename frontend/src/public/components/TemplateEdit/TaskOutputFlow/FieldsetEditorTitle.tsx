import * as React from 'react';
import { useState, useRef, useEffect } from 'react';
import classnames from 'classnames';

import { PencilSmallIcon } from '../../icons';
import { validateFieldsetTitle } from '../../../utils/validators';

import styles from '../OutputForm/OutputForm.css';
import kickoffStyles from '../KickoffRedux/KickoffRedux.css';

import { IFieldsetEditorTitleProps } from './types';

export function FieldsetEditorTitle({
  apiNameBinding,
  title,
  onEditFieldsetTitle,
  formatMessage,
}: IFieldsetEditorTitleProps) {
  const [localTitle, setLocalTitle] = useState(title);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setLocalTitle(title);
  }, [title]);

  const isTitleError = Boolean(validateFieldsetTitle(localTitle));

  const handleBlur = () => {
    setIsFocused(false);
    if (localTitle !== title) {
      onEditFieldsetTitle(apiNameBinding, localTitle);
    }
  };

  return (
    <div
      className={classnames(
        styles['flow__fieldset-title-edit'],
        isTitleError && styles['flow__fieldset-title-edit_error'],
      )}
    >
      <span className={styles['flow__fieldset-label']}>{formatMessage({ id: 'fieldsets.title-label' })}:</span>
      <textarea
        ref={inputRef}
        className={styles['flow__fieldset-title-input']}
        value={localTitle}
        onChange={(event) => setLocalTitle(event.target.value)}
        placeholder={formatMessage({ id: 'fieldsets.settings.title-placeholder' })}
        rows={1}
        onFocus={() => setIsFocused(true)}
        onBlur={handleBlur}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            event.currentTarget.blur();
          }
        }}
      />
      {!isFocused && (
        <button
          onClick={() => inputRef.current?.focus()}
          className={kickoffStyles['kick-off-edit-name']}
        >
          <PencilSmallIcon />
        </button>
      )}
    </div>
  );
}
