import * as React from 'react';
import { useState, useMemo, useCallback } from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';

import { Modal, Button } from '../../UI';
import { UsersDropdownComponent, EOptionTypes, TUsersDropdownOption } from '../../UI/form/UsersDropdown/UsersDropdown';
import { getUsers } from '../../../redux/selectors/user';
import { getAccountsTeamList } from '../../../redux/selectors/accounts';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { openTeamInvitesPopup } from '../../../redux/team/slice';
import styles from './SelectManagerModal.css';

interface ISelectManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (managerId: number | null) => void;
  currentManagerId: number | null;
  currentUserId: number;
}

export function SelectManagerModal({
  isOpen,
  onClose,
  onConfirm,
  currentManagerId,
  currentUserId,
}: ISelectManagerModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  
  const storeUsers = useSelector(getUsers);
  const teamList = useSelector(getAccountsTeamList);
  const allUsers = useMemo(() => {
    const merged = getNotDeletedUsers([...storeUsers, ...teamList]);
    const seen = new Set<number>();
    return merged.filter(user => {
      const id = Number(user.id);
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }, [storeUsers, teamList]);
  
  // Filter out the current user so they can't be their own manager
  const selectableUsers = useMemo(() => allUsers.filter(user => user.id !== currentUserId), [allUsers, currentUserId]);

  const [selectedManager, setSelectedManager] = useState<TUsersDropdownOption | null>(() => {
    if (currentManagerId) {
      const manager = selectableUsers.find(u => u.id === currentManagerId);
      if (manager) {
        return {
          id: manager.id,
          optionType: EOptionTypes.User,
          label: getUserFullName(manager),
          value: String(manager.id),
        } as TUsersDropdownOption;
      }
    }
    return null;
  });

  const selectionsDropdownOption: TUsersDropdownOption[] = useMemo(() => selectableUsers.map((item) => ({
    ...item,
    optionType: EOptionTypes.User,
    label: getUserFullName(item),
    value: String(item.id),
  })), [selectableUsers]);

  const handleConfirm = useCallback(() => {
    onConfirm(selectedManager ? Number(selectedManager.id) : null);
    onClose();
  }, [selectedManager, onConfirm, onClose]);

  const handleRemove = useCallback(() => {
    onConfirm(null);
    onClose();
  }, [onConfirm, onClose]);

  const handleChange = useCallback((option: TUsersDropdownOption | null) => {
    setSelectedManager(option);
  }, []);

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className={styles['select-manager-modal']}>
        <p className={styles['select-manager-modal__title']}>
          Select Manager
        </p>

        <div className={styles['select-manager-modal__content']}>
          <UsersDropdownComponent
            options={selectionsDropdownOption}
            users={allUsers}
            isMulti={false}
            value={selectedManager}
            onChange={handleChange}
            inviteLabel="Invite member"
            isTeamInvitesModalOpen={false}
            recentInvitedUsers={[]}
            isAdmin={false} // don't allow inviting from here initially for simplicity
            openTeamInvitesPopup={() => dispatch(openTeamInvitesPopup())}
            onClickInvite={() => {}}
            placeholder="Search"
          />
        </div>

        <div className={styles['select-manager-modal__buttons']}>
          <Button
            type="button"
            buttonStyle="yellow"
            size="md"
            onClick={handleConfirm}
            label={formatMessage({ id: 'task.return-to.confirm' })}
          />
          {currentManagerId && (
            <Button
              type="button"
              className={styles['select-manager-modal__button-remove']}
              buttonStyle="transparent-orange"
              size="md"
              onClick={handleRemove}
              label={formatMessage({ id: 'button.remove' })}
            />
          )}
        </div>
      </div>
    </Modal>
  );
}
