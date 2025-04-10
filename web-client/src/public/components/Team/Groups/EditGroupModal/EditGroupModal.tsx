import React, { FormEvent, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { editModalClose, updateGroup } from '../../../../redux/actions';
import { validateGroupName } from '../../../../utils/validators';
import { Button, Header, InputField, Modal } from '../../../UI';
import { IApplicationState } from '../../../../types/redux';

import styles from './EditGroupModal.css';

export function EditGroupModal() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const { isOpen, editGroup } = useSelector(({ groups }: IApplicationState) => groups.editModal);

  const [inputName, setInputName] = useState('');
  const [changedInput, setChangedInput] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setInputName(editGroup?.name || '');
    setChangedInput(false);
  }, [editGroup]);

  const validationForm = () => {
    const currentError = validateGroupName(inputName);
    if (currentError) {
      setError(currentError);
      return false;
    }

    return true;
  };

  const handleCloseModal = () => {
    dispatch(editModalClose());
    setError('');
    setInputName('');
  };

  const handleEditGroup = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validationForm()) return;
    if (editGroup) {
      dispatch(
        updateGroup({
          ...editGroup,
          name: inputName,
        }),
      );
    }

    setInputName('');
    handleCloseModal();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['tenant-modal__title']}>
          {formatMessage({ id: 'team.groups.edit-modal.title' })}
        </Header>
        <p className={styles['tenant-modal__description']}>{formatMessage({ id: 'team.groups.edit-modal.caption' })}</p>
        <form onSubmit={(e) => handleEditGroup(e)} data-autofocus-first-field>
          <InputField
            autoFocus
            value={inputName}
            onChange={(e) => {
              setChangedInput(true);
              setInputName(e.currentTarget.value);
            }}
            errorMessage={error}
            fieldSize="md"
            placeholder=""
          />
          <div className={styles['tenant-modal__footer']}>
            <Button
              type="submit"
              label={formatMessage({ id: 'team.groups.edit-modal.confirm' })}
              buttonStyle="yellow"
              size="md"
              disabled={!inputName || !changedInput}
            />
            <button type="button" className="cancel-button" onClick={handleCloseModal}>
              {formatMessage({ id: 'tenants.modal-button-cancel' })}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
