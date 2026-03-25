import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { TUserListItem } from '../../../types/user';
import { IVacationActivateRequest, activateVacation, deactivateVacation } from '../../../api/vacation';
import { VacationSettings } from '../../VacationSettings';
import { Modal } from '../../UI/Modal';
import { NotificationManager } from '../../UI/Notifications';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { teamFetchStarted, usersFetchStarted } from '../../../redux/accounts/slice';
import { getAccountsUsers } from '../../../redux/selectors/accounts';

export interface IVacationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: TUserListItem | null;
}

export function VacationSettingsModal({ isOpen, onClose, user }: IVacationSettingsModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(false);

  const availableUsers: TUserListItem[] = useSelector(getAccountsUsers).filter(
    (u: TUserListItem) => u.id !== user?.id && u.status === 'active'
  );

  const handleActivate = async (data: IVacationActivateRequest) => {
    if (!user?.id) return;
    setIsLoading(true);
    try {
      await activateVacation(data, user.id);
      NotificationManager.success({ message: formatMessage({ id: 'user-info.vacation.activated-success' }) });
      dispatch(teamFetchStarted({}));
      dispatch(usersFetchStarted());
      onClose();
    } catch (error) {
      NotificationManager.notifyApiError(error, { title: 'error.general', message: getErrorMessage(error) });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeactivate = async () => {
    if (!user?.id) return;
    setIsLoading(true);
    try {
      await deactivateVacation(user.id);
      NotificationManager.success({ message: formatMessage({ id: 'user-info.vacation.deactivated-success' }) });
      dispatch(teamFetchStarted({}));
      dispatch(usersFetchStarted());
      onClose();
    } catch (error) {
      NotificationManager.notifyApiError(error, { title: 'error.general', message: getErrorMessage(error) });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      width="lg"
    >
      {user ? (
        <div style={{ padding: '0 24px 24px' }}>
          <VacationSettings
            isAbsent={!!user.isAbsent}
            absenceStatus={user.absenceStatus || 'vacation'}
            vacationStartDate={user.vacationStartDate || null}
            vacationEndDate={user.vacationEndDate || null}
            substituteUserIds={user.substituteUserIds || []}
            availableUsers={availableUsers}
            onActivate={handleActivate}
            onDeactivate={handleDeactivate}
            isLoading={isLoading}
          />
        </div>
      ) : null}
    </Modal>
  );
}
