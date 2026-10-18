import * as React from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { InputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import type { ICreateApiKeyModalProps, INewApiKeyModalProps, IRevokeApiKeyModalProps } from './types';

import styles from '../IntegrationsCommon.css';

export function NewApiKeyModal({ apiKey, onClose, onCopy }: INewApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={!!apiKey} onClose={onClose} width="sm">
      <div data-testid="new-key-modal">
        <Header tag="p" size="6" className={styles['create-modal__title']}>
          {formatMessage({ id: 'integrations.api-key-created-title' })}
        </Header>
        <p className={styles['api-keys__modal-warning']}>
          {formatMessage({ id: 'integrations.api-key-created-warning' })}
        </p>
        <div className={styles['api-keys__modal-key']}>
          <code className={styles['api-keys__modal-key-value']} data-testid="raw-key-value">
            {apiKey}
          </code>
          <button
            type="button"
            className={styles['api-keys__modal-copy-btn']}
            onClick={onCopy}
            data-testid="copy-inline-btn"
          >
            {formatMessage({ id: 'team.create-user-modal.copy' })}
          </button>
        </div>
        <div className={styles['create-modal__footer']}>
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

export function RevokeApiKeyModal({ isOpen, onClose, onConfirm }: IRevokeApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="sm">
      <div data-testid="revoke-key-modal">
        <Header tag="p" size="6" className={styles['create-modal__title']}>
          {formatMessage({ id: 'integrations.revoke-modal-title' })}
        </Header>
        <p className={styles['api-keys__modal-warning']}>
          {formatMessage({ id: 'integrations.delete-api-key-confirm' })}
        </p>
        <div className={styles['create-modal__footer']}>
          <Button
            type="button"
            onClick={onConfirm}
            size="md"
            buttonStyle="yellow"
            label={formatMessage({ id: 'integrations.api-key-revoke' })}
            data-testid="confirm-revoke-btn"
          />
          <button type="button" className="cancel-button" onClick={onClose} data-testid="cancel-revoke-btn">
            {formatMessage({ id: 'integrations.cancel' })}
          </button>
        </div>
      </div>
    </Modal>
  );
}

export function CreateApiKeyModal({ isOpen, name, onNameChange, onSubmit, onClose }: ICreateApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="sm">
      <div data-testid="create-key-modal">
        <Header tag="p" size="6" className={styles['create-modal__title']}>
          {formatMessage({ id: 'integrations.create-api-key-modal-title' })}
        </Header>
        <p className={styles['create-modal__description']}>
          {formatMessage({ id: 'integrations.create-api-key-modal-description' })}
        </p>
        <form onSubmit={onSubmit} data-autofocus-first-field>
          <InputField
            autoFocus
            value={name}
            onChange={onNameChange}
            placeholder={formatMessage({ id: 'integrations.api-key-name-placeholder' })}
            fieldSize="md"
            data-testid="api-key-name-input"
          />
          <div className={styles['create-modal__footer']}>
            <Button
              type="submit"
              size="md"
              buttonStyle="yellow"
              label={formatMessage({ id: 'integrations.create-api-key' })}
              data-testid="submit-create-key"
            />
            <button type="button" className="cancel-button" onClick={onClose} data-testid="cancel-create-key">
              {formatMessage({ id: 'integrations.cancel' })}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
