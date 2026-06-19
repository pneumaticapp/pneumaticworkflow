import * as React from 'react';
import { useState, useMemo, useCallback } from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';

import { Modal, Button } from '../../UI';
import { UsersDropdownComponent, EOptionTypes, TUsersDropdownOption } from '../../UI/form/UsersDropdown/UsersDropdown';
import { getUsers } from '../../../redux/selectors/user';
import { getNotDeletedUsers, getUserFullName } from '../../../utils/users';
import { openTeamInvitesPopup } from '../../../redux/team/slice';
import { UserPerformer, EBgColorTypes } from '../../UI/UserPerformer';
import { ETaskPerformerType } from '../../../types/template';
import styles from './SelectReportsModal.css';

interface ISelectReportsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reportIds: number[]) => void;
  currentReportIds: number[];
  currentUserId: number;
  isLoading?: boolean;
}

export function SelectReportsModal({
  isOpen,
  onClose,
  onConfirm,
  currentReportIds,
  currentUserId,
  isLoading,
}: ISelectReportsModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  
  const allUsers = getNotDeletedUsers(useSelector(getUsers));
  
  // Filter out the current user so they can't be their own report
  const selectableUsers = useMemo(() => allUsers.filter(user => user.id !== currentUserId), [allUsers, currentUserId]);

  const [selectedReports, setSelectedReports] = useState<TUsersDropdownOption[]>(() => {
    return currentReportIds.map(id => {
      const report = selectableUsers.find(u => u.id === id);
      if (report) {
        return {
          id: report.id,
          optionType: EOptionTypes.User,
          label: getUserFullName(report),
          value: String(report.id),
        } as TUsersDropdownOption;
      }
      return null;
    }).filter(Boolean) as TUsersDropdownOption[];
  });

  const selectionsDropdownOption: TUsersDropdownOption[] = useMemo(() => selectableUsers.map((item) => ({
    ...item,
    optionType: EOptionTypes.User,
    label: getUserFullName(item),
    value: String(item.id),
  })), [selectableUsers]);

  const handleConfirm = useCallback(() => {
    onConfirm(selectedReports.map(opt => Number(opt.id)));
  }, [selectedReports, onConfirm]);

  const handleAddReport = useCallback((option: TUsersDropdownOption) => {
    setSelectedReports(prev => {
      if (prev.find(p => p.id === option.id)) return prev;
      return [...prev, option];
    });
  }, []);

  const handleRemoveReport = useCallback((option: TUsersDropdownOption) => {
    setSelectedReports(prev => prev.filter(p => p.id !== option.id));
  }, []);

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className={styles['select-reports-modal']}>
        <p className={styles['select-reports-modal__title']}>
          Select Reports
        </p>

        <div className={styles['select-reports-modal__content']}>
          <UsersDropdownComponent
            options={selectionsDropdownOption}
            users={allUsers as any}
            isMulti
            value={selectedReports}
            onChange={handleAddReport as any}
            onChangeSelected={handleRemoveReport as any}
            inviteLabel="Invite member"
            isTeamInvitesModalOpen={false}
            recentInvitedUsers={[]}
            isAdmin={false} // don't allow inviting from here initially for simplicity
            openTeamInvitesPopup={() => dispatch(openTeamInvitesPopup())}
            onClickInvite={() => {}}
            placeholder="Search"
          />
          <ul className={styles['select-reports-modal__performers']}>
            {selectedReports.map((report) => (
              <li key={report.id} className={styles['select-reports-modal__performer-item']}>
                <UserPerformer
                  user={{
                    ...report,
                    type: ETaskPerformerType.User,
                    sourceId: String(report.id),
                  }}
                  bgColor={EBgColorTypes.Light}
                  onClick={() => handleRemoveReport(report)}
                />
              </li>
            ))}
          </ul>
        </div>

        <div className={styles['select-reports-modal__buttons']}>
          <Button
            type="button"
            buttonStyle="yellow"
            size="md"
            onClick={handleConfirm}
            label={formatMessage({ id: 'task.return-to.confirm' })}
            disabled={isLoading}
          />
        </div>
      </div>
    </Modal>
  );
}
