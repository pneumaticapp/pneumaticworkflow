import React, { FormEvent, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { validateTenantName } from '../../../../utils/validators';
import { Button, Header, InputField, Modal } from '../../../UI';
import { IApplicationState } from '../../../../types/redux';
import { createGroup, createModalClose } from '../../../../redux/actions';

import styles from './CreateGroupModal.css';

export function CreateGroupModal() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const { createModal: isOpen } = useSelector((state: IApplicationState) => state.groups);

  const [inputName, setInputName] = useState(formatMessage({ id: 'team.groups.create-modal.new-group' }));
  const [error, setError] = useState('');

  const validationForm = () => {
    const currentError = validateTenantName(inputName);
    if (currentError) {
      setError(currentError);
      return false;
    }

    return true;
  };

  const handleCloseModal = () => {
    dispatch(createModalClose());
    setInputName(formatMessage({ id: 'team.groups.create-modal.new-group' }));
    setError('');
  };

  const handleCreateGroup = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validationForm()) return;
    dispatch(
      createGroup({
        name: inputName,
        photo: null,
        users: [],
        id: -1,
      }),
    );

    setInputName('');
    handleCloseModal();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['tenant-modal__title']}>
          {formatMessage({ id: 'team.groups.create-modal.title' })}
        </Header>
        <p className={styles['tenant-modal__description']}>
          {formatMessage({ id: 'team.groups.create-modal.caption' })}
        </p>
        <form onSubmit={(e) => handleCreateGroup(e)} data-autofocus-first-field>
          <InputField
            autoFocus
            value={inputName}
            onChange={(e) => setInputName(e.currentTarget.value)}
            errorMessage={error}
            fieldSize="md"
          />
          <div className={styles['tenant-modal__footer']}>
            <Button type="submit" label="Create" buttonStyle="yellow" size="md" disabled={!inputName} />
            <button type="button" className="cancel-button" onClick={handleCloseModal}>
              {formatMessage({ id: 'tenants.modal-button-cancel' })}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
