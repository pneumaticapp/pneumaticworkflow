import React from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import type { INewApiKeyModalProps } from './types';

import styles from './ApiKeys.css';

export function NewApiKeyModal({ apiKey, onClose, onCopy }: INewApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={!!apiKey} onClose={onClose} width="sm">
      <div data-testid="new-key-modal">
        <Header tag="h2" size="6" className={styles['key-modal__title']}>
          {formatMessage({ id: 'integrations.api-key-created-title' })}
        </Header>
        <p className={styles['key-modal__warning']}>{formatMessage({ id: 'integrations.api-key-created-warning' })}</p>
        <div className={styles['key-modal__key']}>
          <code className={styles['key-modal__key-value']} data-testid="raw-key-value">
            {apiKey}
          </code>
          <button
            type="button"
            className={styles['key-modal__copy-btn']}
            onClick={onCopy}
            data-testid="copy-inline-btn"
          >
            {formatMessage({ id: 'team.create-user-modal.copy' })}
          </button>
        </div>
        <div className={styles['key-modal__footer']}>
          <Button
            type="button"
            onClick={onClose}
            size="md"
            label={formatMessage({ id: 'integrations.api-key-done' })}
            data-testid="done-key-btn"
          />
        </div>
      </div>
    </Modal>
  );
}
