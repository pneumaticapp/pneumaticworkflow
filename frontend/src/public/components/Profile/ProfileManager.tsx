import * as React from 'react';
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getUsers } from '../../redux/selectors/user';
import { getAccountsTeamList } from '../../redux/selectors/accounts';
import { getNotDeletedUsers, getUserFullName } from '../../utils/users';
import { SelectManagerModal } from '../Team/SelectManagerModal';
import { Button, Header } from '../UI';
import { SectionTitle } from '../UI/Typeography/SectionTitle';
import { Avatar } from '../UI/Avatar';

import styles from './Profile.css';

interface IProfileManagerProps {
  currentUserId: number;
  managerId: number | null;
  onManagerChange: (managerId: number | null) => void;
}

export function ProfileManager({ currentUserId, managerId, onManagerChange }: IProfileManagerProps) {
  const { formatMessage } = useIntl();
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const allUsers = useSelector(getUsers);
  const teamList = useSelector(getAccountsTeamList);
  const users = getNotDeletedUsers([...allUsers, ...teamList]);
  
  const manager = managerId ? users.find(u => Number(u.id) === Number(managerId)) : null;

  return (
    <div className={styles['manager-section']}>
      <SectionTitle className={styles['fields-group__title']}>
        Manager
      </SectionTitle>

      {manager ? (
        <>
          <div className={styles['manager-card']}>
            <div className={styles['manager-card__info']}>
              <Avatar user={manager} size="md" />
              <div className={styles['manager-card__details']}>
                <Header size="6" tag="p" className={styles['manager-card__header']}>
                  {getUserFullName(manager)}
                </Header>
                <p className={styles['manager-card__subheader']}>
                  <strong>{formatMessage({ id: 'team.user-id' }, { id: manager.id })}</strong>{' '}
                  {formatMessage({ id: 'team.user-email' }, { email: manager.email })}
                </p>
              </div>
            </div>
          </div>
          <Button
            type="button"
            onClick={() => setIsModalOpen(true)}
            label="Change manager"
            buttonStyle="transparent-black"
            size="sm"
            className={styles['manager-card__edit-btn']}
          />
        </>
      ) : (
        <Button
          type="button"
          onClick={() => setIsModalOpen(true)}
          label="Add manager"
          buttonStyle="transparent-black"
          size="sm"
        />

      )}

      {isModalOpen && (
        <SelectManagerModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onConfirm={(newManagerId) => onManagerChange(newManagerId)}
          currentManagerId={managerId}
          currentUserId={currentUserId}
        />
      )}
    </div>
  );
}
