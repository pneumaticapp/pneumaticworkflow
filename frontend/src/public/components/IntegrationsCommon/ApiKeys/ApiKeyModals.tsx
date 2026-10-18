import * as React from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { FormikInputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import type {
  ICreateApiKeyFormValues,
  ICreateApiKeyModalProps,
  INewApiKeyModalProps,
  IRevokeApiKeyModalProps,
} from './types';

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

export function RevokeApiKeyModal({ isOpen, onClose, onConfirm }: IRevokeApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="sm">
      <div data-testid="revoke-key-modal">
        <Header tag="h2" size="6" className={styles['key-modal__title']}>
          {formatMessage({ id: 'integrations.revoke-modal-title' })}
        </Header>
        <p className={styles['key-modal__warning']}>{formatMessage({ id: 'integrations.delete-api-key-confirm' })}</p>
        <div className={styles['key-modal__footer']}>
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

export function CreateApiKeyModal({ isOpen, onSubmit, onClose }: ICreateApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="sm">
      <div data-testid="create-key-modal">
        <Header tag="h2" size="6" className={styles['key-modal__title']}>
          {formatMessage({ id: 'integrations.create-api-key-modal-title' })}
        </Header>
        <p className={styles['key-modal__description']}>
          {formatMessage({ id: 'integrations.create-api-key-modal-description' })}
        </p>
        <Formik<ICreateApiKeyFormValues> initialValues={{ name: '' }} onSubmit={({ name }) => onSubmit(name.trim())}>
          {({ handleSubmit }) => (
            <form onSubmit={handleSubmit} data-autofocus-first-field>
              <FormikInputField
                autoFocus
                name="name"
                placeholder={formatMessage({ id: 'integrations.api-key-name-placeholder' })}
                fieldSize="md"
                data-testid="api-key-name-input"
              />
              <div className={styles['key-modal__footer']}>
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
          )}
        </Formik>
      </div>
    </Modal>
  );
}
