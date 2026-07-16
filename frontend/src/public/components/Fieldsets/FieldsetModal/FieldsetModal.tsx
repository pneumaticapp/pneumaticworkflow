import * as React from 'react';
import { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { validateFieldsetName } from '../../../utils/validators';
import { Button, Header, InputField, Modal } from '../../UI';
import {
  closeCreateModal,
  closeEditModal,
  createFieldsetAction,
  updateFieldsetAction,
} from '../../../redux/fieldsets/slice';
import {
  isCreateModalOpen,
  isEditModalOpen,
  getCurrentFieldset,
} from '../../../redux/selectors/fieldsets';

import { EFieldsetModalType, IFieldsetModalProps } from './types';
import styles from './FieldsetModal.css';

const CONFIG = {
  [EFieldsetModalType.Create]: {
    title: 'fieldsets.new-fieldset.title',
    description: 'fieldsets.new-fieldset.description',
    submitLabel: 'fieldsets.modal-button-create',
    isModalOpenSelector: isCreateModalOpen,
    closeAction: closeCreateModal,
    placeholder: 'fieldsets.new-fieldset.title',
  },
  [EFieldsetModalType.Edit]: {
    title: 'fieldsets.edit-fieldset.title',
    description: 'fieldsets.edit-fieldset.description',
    submitLabel: 'fieldsets.modal-button-confirm',
    isModalOpenSelector: isEditModalOpen,
    closeAction: closeEditModal,
    placeholder: '',
  },
};

export function FieldsetModal({ type }: IFieldsetModalProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const { title, description, submitLabel, isModalOpenSelector, closeAction, placeholder } = CONFIG[type];
  const isOpen = useSelector(isModalOpenSelector);
  const currentFieldset = useSelector(getCurrentFieldset);

  const [inputName, setInputName] = useState('');
  const [error, setError] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setInputName(type === EFieldsetModalType.Edit && currentFieldset ? currentFieldset.name : '');
      setError('');
      setHasChanges(false);
    }
  }, [isOpen, currentFieldset, type]);

  const validationForm = () => {
    const currentError = validateFieldsetName(inputName);
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
      setError(validateFieldsetName(newValue));
    }
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validationForm()) return;

    if (type === EFieldsetModalType.Create) {
      dispatch(createFieldsetAction({ name: inputName }));
    } else if (currentFieldset) {
      dispatch(updateFieldsetAction({ id: currentFieldset.id, name: inputName }));
    }
    handleCloseModal();
  };

  const isSubmitDisabled = !inputName || (type === EFieldsetModalType.Edit && !hasChanges);

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['fieldset-modal__title']}>
          {formatMessage({ id: title })}
        </Header>
        <p className={styles['fieldset-modal__description']}>
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
          <div className={styles['fieldset-modal__footer']}>
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
              label={formatMessage({ id: 'fieldsets.modal-button-cancel' })}
              onClick={handleCloseModal}
            />
          </div>
        </form>
      </div>
    </Modal>
  );
}
