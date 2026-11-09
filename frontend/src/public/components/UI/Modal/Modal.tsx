import * as React from 'react';
import { Modal as BootstrapModal } from 'reactstrap';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ClearIcon } from '../../icons';

import styles from './Modal.css';

interface IModalProps {
  isOpen: boolean;
  children: React.ReactNode;
  width?: 'sm' | 'lg';
  onClose?(): void;
}

export function Modal({ isOpen, children, width = 'sm', onClose }: IModalProps) {
  const { formatMessage } = useIntl();
  return (
    <BootstrapModal
      isOpen={isOpen}
      toggle={onClose}
      centered
      zIndex={1080}
      className={classnames(styles['modal'], width === 'sm' ? styles['modal_sm'] : styles['modal_lg'])}
      contentClassName={styles['modal-content']}
      backdropClassName={styles['backdrop']}
    >
      {onClose && (
        <button
          onClick={onClose}
          type="button"
          className={styles['close-button']}
          aria-label={formatMessage({ id: 'general.close' })}
          data-test-id="close"
        >
          <ClearIcon />
        </button>
      )}
      {children}
    </BootstrapModal>
  );
}
