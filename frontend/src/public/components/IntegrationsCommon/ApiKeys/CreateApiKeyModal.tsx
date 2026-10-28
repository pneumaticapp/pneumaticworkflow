import * as React from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { FormikInputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import type { ICreateApiKeyFormValues, ICreateApiKeyModalProps } from './types';

import styles from './ApiKeys.css';

export function CreateApiKeyModal({ isOpen, onSubmit, onClose }: ICreateApiKeyModalProps) {
  const { formatMessage } = useIntl();

  const handleSubmit = ({ name }: ICreateApiKeyFormValues) => {
    onSubmit(name.trim());
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="sm">
      <div data-testid="create-key-modal">
        <Header tag="h2" size="6" className={styles['key-modal__title']}>
          {formatMessage({ id: 'integrations.create-api-key-modal-title' })}
        </Header>
        <p className={styles['key-modal__description']}>
          {formatMessage({ id: 'integrations.create-api-key-modal-description' })}
        </p>
        <Formik<ICreateApiKeyFormValues> initialValues={{ name: '' }} onSubmit={handleSubmit}>
          {({ handleSubmit: formikSubmit }) => (
            <form onSubmit={formikSubmit} data-autofocus-first-field>
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
