import * as React from 'react';
import TextareaAutosize from 'react-textarea-autosize';
import * as classnames from 'classnames';

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
}

export function EditableText({
  isLoading,
  text,
  className,
  placeholder,
  editButtonHint,
  onChangeText,
}: IEditableTextProps) {
  const [isEditing, setIsEditing] = React.useState(false);

  const startEditState = () => setIsEditing(true);

  if (!isEditing) {
    return (
      <div
        className={classnames(className, styles['text'])}
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
    );
  }

  const handleEditName = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    event.preventDefault();
    const trimmedText = event.target.value.trim();
    if (trimmedText !== text) {
      onChangeText(trimmedText);
    }
  };

  return (
    <form className={className}>
      <Loader isLoading={isLoading} />
      <TextareaAutosize
        translate={undefined}
        onFocus={(e) => e.currentTarget.setSelectionRange(e.currentTarget.value.length, e.currentTarget.value.length)}
        onBlur={() => setIsEditing(false)}
        autoFocus
        value={text}
        onChange={(e) => handleEditName(e)}
        className={styles['textarea']}
        placeholder={placeholder}
        spellCheck={false}
      />
    </form>
  );
}
