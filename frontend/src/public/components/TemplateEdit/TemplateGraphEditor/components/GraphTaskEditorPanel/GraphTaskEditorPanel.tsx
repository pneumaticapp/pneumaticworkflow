import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useIntl } from 'react-intl';

import { ModalCloseIcon } from '../../../../icons';
import { IGraphTaskEditorPanelProps } from '../../types';

import styles from './GraphTaskEditorPanel.css';

export const GraphTaskEditorPanel = ({ children, onClose }: IGraphTaskEditorPanelProps) => {
  const { formatMessage } = useIntl();

  return ReactDOM.createPortal(
    <>
      <button
        type="button"
        className={styles['graph-task-editor__overlay']}
        aria-label={formatMessage({ id: 'template.graph-task-editor-close' })}
        data-test-id="graph-task-editor-overlay"
        onClick={onClose}
      />
      <aside
        className={styles['graph-task-editor']}
        data-test-id="graph-task-editor"
        aria-label={formatMessage({ id: 'template.graph-task-editor' })}
      >
        <button
          type="button"
          className={styles['graph-task-editor__close']}
          aria-label={formatMessage({ id: 'template.graph-task-editor-close' })}
          data-test-id="graph-task-editor-close"
          onClick={onClose}
        >
          <ModalCloseIcon fill="currentColor" />
        </button>
        <div className={styles['graph-task-editor__body']}>{children}</div>
      </aside>
    </>,
    document.body,
  );
};
