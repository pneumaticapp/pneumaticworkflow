import React, { FormEvent, useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { validateDatasetName } from '../../../utils/validators';
import { Button, Header, InputField, Modal } from '../../UI';
import { closeCreateModal, createDatasetAction } from '../../../redux/datasets/slice';
import { isCreateModalOpen } from '../../../redux/selectors/datasets';

import styles from './DatasetModal.css';

export function DatasetModal() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const isOpen = useSelector(isCreateModalOpen);

  const [inputName, setInputName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setInputName('');
      setError('');
    }
  }, [isOpen]);

  const validationForm = () => {
    const currentError = validateDatasetName(inputName);
    if (currentError) {
      setError(currentError);
      return false;
    }

    return true;
  };

  const handleCloseModal = () => {
    dispatch(closeCreateModal());
    setError('');
  };

  const handleCreateDataset = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validationForm()) return;
    dispatch(
      createDatasetAction({
        name: inputName,
      })
    );
    handleCloseModal();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['dataset-modal__title']}>
          {formatMessage({ id: 'datasets.new-dataset.title' })}
        </Header>
        <p className={styles['dataset-modal__description']}>
          {formatMessage({ id: 'datasets.new-dataset.description' })}
        </p>
        <form onSubmit={handleCreateDataset} data-autofocus-first-field>
          <InputField
            autoFocus
            value={inputName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputName(e.currentTarget.value)}
            errorMessage={error}
            fieldSize="md"
            placeholder={formatMessage({ id: 'datasets.new-dataset.title' })}
          />
          <div className={styles['dataset-modal__footer']}>
            <Button type="submit" label={formatMessage({ id: 'datasets.modal-button-create' })} buttonStyle="yellow" size="md" disabled={!inputName} />
            <Button
              type="button"
              buttonStyle="link-dark-text"
              label={formatMessage({ id: 'datasets.modal-button-cancel' })}
              onClick={handleCloseModal}
            />
          </div>
        </form>
      </div>
    </Modal>
  );
}
