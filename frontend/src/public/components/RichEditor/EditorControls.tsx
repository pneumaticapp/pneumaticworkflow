import * as React from 'react';
import classnames from 'classnames';
import { IntlMessages } from '../IntlMessages';
import styles from './RichEditor.css';

export interface IEditorControlsProps {
  onSubmit?: () => void;
  onCancel?: () => void;
  handleSubmit: () => void;
  handleCancel: () => void;
  shouldSubmitAfterFileLoaded: boolean;
  submitIcon?: React.ReactNode;
  cancelIcon?: React.ReactNode;
}

export function EditorControls({
  onSubmit,
  onCancel,
  handleSubmit,
  handleCancel,
  shouldSubmitAfterFileLoaded,
  submitIcon,
  cancelIcon,
}: IEditorControlsProps) {
  if (!onSubmit) return null;

  return (
    <div className={styles['actions']}>
      <div className={styles['controls']}>
        {onCancel && (
          <button
            type="button"
            className={classnames('cancel-button', styles['controls__send-button'])}
            onClick={handleCancel}
            disabled={shouldSubmitAfterFileLoaded}
          >
            {cancelIcon ?? <IntlMessages id="workflows.log-cancel-send-comment" />}
          </button>
        )}
        <button
          type="button"
          className={classnames('cancel-button', styles['controls__send-button'])}
          onClick={handleSubmit}
          disabled={shouldSubmitAfterFileLoaded}
        >
          {submitIcon ?? <IntlMessages id="workflows.log-send-comment" />}
        </button>
      </div>
    </div>
  );
}
