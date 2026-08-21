import * as React from 'react';
import { useRef } from 'react';
import * as ReactDOM from 'react-dom';
import { useIntl } from 'react-intl';

import { useCloseOnOutsideClick } from '../../../../../hooks/useCloseOnOutsideClick';
import { ModalCloseIcon } from '../../../../icons';
import { IGraphTaskEditorPanelProps } from '../../types';

import styles from './GraphTaskEditorPanel.css';

export const GraphTaskEditorPanel = ({ children, onClose }: IGraphTaskEditorPanelProps) => {
  const { formatMessage } = useIntl();
  const panelRef = useRef<HTMLElement>(null);

  useCloseOnOutsideClick(panelRef, onClose);

  return ReactDOM.createPortal(
    <aside
      ref={panelRef}
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
    </aside>,
    document.body,
  );
};
