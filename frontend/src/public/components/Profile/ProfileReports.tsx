import * as React from 'react';
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { getUsers } from '../../redux/selectors/user';
import { getAccountsTeamList } from '../../redux/selectors/accounts';
import { getNotDeletedUsers, getUserFullName } from '../../utils/users';
import { SelectReportsModal } from '../Team/SelectReportsModal';
import { Button, Header } from '../UI';
import { SectionTitle } from '../UI/Typeography/SectionTitle';
import { Avatar } from '../UI/Avatar';
import { IUpdateUserRequest } from '../../api/editProfile';

import styles from './Profile.css';

interface IProfileReportsProps {
  currentUserId: number;
  reportIds: number[] | undefined;
  editCurrentUser(body: IUpdateUserRequest): void;
}

export function ProfileReports({ currentUserId, reportIds = [], editCurrentUser }: IProfileReportsProps) {
  const { formatMessage } = useIntl();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const allUsers = useSelector(getUsers);
  const teamList = useSelector(getAccountsTeamList);
  const users = getNotDeletedUsers([...allUsers, ...teamList]);
  
  const reports = reportIds.map(id => users.find(u => Number(u.id) === Number(id))).filter(Boolean) as typeof users;

  const handleReportsChange = (newReportIds: number[]) => {
    editCurrentUser({ subordinates: newReportIds });
  };

  return (
    <div className={styles['manager-section']}>
      <SectionTitle className={styles['fields-group__title']}>
        Reports
      </SectionTitle>

      {reports && reports.length > 0 ? (
        <>
          {reports.map((report) => (
            <div key={report.id} className={styles['manager-card']}>
              <div className={styles['manager-card__info']}>
                <Avatar user={report} size="md" />
                <div className={styles['manager-card__details']}>
                  <Header size="6" tag="p" className={styles['manager-card__header']}>
                    {getUserFullName(report)}
                  </Header>
                  <p className={styles['manager-card__subheader']}>
                    <strong>{formatMessage({ id: 'team.user-id' }, { id: report.id })}</strong>{' '}
                    {formatMessage({ id: 'team.user-email' }, { email: report.email })}
                  </p>
                </div>
              </div>
            </div>
          ))}
          <Button
            type="button"
            onClick={() => setIsModalOpen(true)}
            label="Edit reports"
            buttonStyle="transparent-black"
            size="sm"
            className={styles['manager-card__edit-btn']}
          />
        </>
      ) : (
        <Button
          type="button"
          onClick={() => setIsModalOpen(true)}
          label="Add reports"
          buttonStyle="transparent-black"
          size="sm"
        />
      )}

      {isModalOpen && (
        <SelectReportsModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onConfirm={handleReportsChange}
          currentReportIds={reportIds}
          currentUserId={currentUserId}
        />
      )}
    </div>
  );
}
