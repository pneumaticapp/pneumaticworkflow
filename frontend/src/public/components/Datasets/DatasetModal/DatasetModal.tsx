import * as React from 'react';
import { useState, FormEvent, ChangeEvent } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { validateDatasetName } from '../../../utils/validators';
import { Button, Header, InputField, Modal } from '../../UI';
import {
  closeCreateModal,
  closeEditModal,
  createDatasetAction,
  updateDatasetAction,
} from '../../../redux/datasets/slice';
import { isCreateModalOpen, isEditModalOpen, getCurrentDataset } from '../../../redux/selectors/datasets';

import { EDatasetModalType, IDatasetModalProps } from './types';
import styles from './DatasetModal.css';

const CONFIG = {
  [EDatasetModalType.Create]: {
    title: 'datasets.new-dataset.title',
    description: 'datasets.new-dataset.description',
    submitLabel: 'datasets.modal-button-create',
    isModalOpenSelector: isCreateModalOpen,
    closeAction: closeCreateModal,
    placeholder: 'datasets.new-dataset.title',
  },
  [EDatasetModalType.Edit]: {
    title: 'datasets.edit-dataset.title',
    description: 'datasets.edit-dataset.description',
    submitLabel: 'datasets.modal-button-confirm',
    isModalOpenSelector: isEditModalOpen,
    closeAction: closeEditModal,
    placeholder: '',
  },
};

export function DatasetModal({ type }: IDatasetModalProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const { title, description, submitLabel, isModalOpenSelector, closeAction, placeholder } = CONFIG[type];
  const isOpen = useSelector(isModalOpenSelector);
  const currentDataset = useSelector(getCurrentDataset);

  const initialName = type === EDatasetModalType.Edit && currentDataset ? currentDataset.name : '';

  const [inputName, setInputName] = useState(initialName);
  const [error, setError] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const validationForm = () => {
    const currentError = validateDatasetName(inputName);
    if (currentError) {
      setError(currentError);
      return false;
    }

    return true;
  };

  const handleCloseModal = () => {
    dispatch(closeAction());
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newValue = e.currentTarget.value;
    setHasChanges(true);
    setInputName(newValue);

    if (error) {
      setError(validateDatasetName(newValue));
    }
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validationForm()) return;

    if (type === EDatasetModalType.Create) {
      dispatch(createDatasetAction({ name: inputName }));
    } else if (currentDataset) {
      dispatch(updateDatasetAction({ id: currentDataset.id, name: inputName }));
    }
    handleCloseModal();
  };

  const isSubmitDisabled = !inputName || (type === EDatasetModalType.Edit && !hasChanges);

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['dataset-modal__title']}>
          {formatMessage({ id: title })}
        </Header>
        <p className={styles['dataset-modal__description']}>
          {formatMessage({ id: description })}
        </p>
        <form onSubmit={handleSubmit} data-autofocus-first-field>
          <InputField
            autoFocus
            value={inputName}
            onChange={handleInputChange}
            errorMessage={error}
            fieldSize="md"
            placeholder={placeholder ? formatMessage({ id: placeholder }) : ''}
          />
          <div className={styles['dataset-modal__footer']}>
            <Button
              type="submit"
              label={formatMessage({ id: submitLabel })}
              buttonStyle="yellow"
              size="md"
              disabled={isSubmitDisabled}
            />
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
