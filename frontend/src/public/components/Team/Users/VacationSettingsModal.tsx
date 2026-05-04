import * as React from 'react';
import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { TUserListItem, isUserAbsent } from '../../../types/user';
import { IVacationActivateRequest, activateVacation, deactivateVacation } from '../../../api/vacation';
import { VacationSettings } from '../../VacationSettings';
import { Modal } from '../../UI/Modal';
import { NotificationManager } from '../../UI/Notifications';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { teamFetchStarted, usersFetchStarted } from '../../../redux/accounts/slice';
import { getAccountsUsers } from '../../../redux/selectors/accounts';
import { getAuthUser } from '../../../redux/selectors/user';
import { vacationSuccess } from '../../../redux/auth/actions';

import styles from './VacationSettingsModal.css';

export interface IVacationSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: TUserListItem | null;
}

export function VacationSettingsModal({ isOpen, onClose, user }: IVacationSettingsModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(false);
  const { authUser } = useSelector(getAuthUser);

  const availableUsers: TUserListItem[] = useSelector(getAccountsUsers).filter(
    (u: TUserListItem) => u.id !== user?.id && u.status === 'active'
  );

  const handleActivate = async (data: IVacationActivateRequest) => {
    if (!user?.id) return;
    setIsLoading(true);
    try {
      const result = await activateVacation(data, user.id);
      NotificationManager.success({ message: formatMessage({ id: 'user-info.vacation.activated-success' }) });
      dispatch(teamFetchStarted({}));
      dispatch(usersFetchStarted());
      
      if (authUser.id === user.id && result) {
        dispatch(vacationSuccess({
          vacation: result.vacation || null,
        }));
      }

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
      const result = await deactivateVacation(user.id);
      NotificationManager.success({ message: formatMessage({ id: 'user-info.vacation.deactivated-success' }) });
      dispatch(teamFetchStarted({}));
      dispatch(usersFetchStarted());

      if (authUser.id === user.id && result) {
        dispatch(vacationSuccess({
          vacation: result.vacation || null,
        }));
      }

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
        <div className={styles['modal-body']}>
          <VacationSettings
            isAbsent={isUserAbsent(user)}
            absenceStatus={user.vacation?.absenceStatus || 'vacation'}
            vacationStartDate={user.vacation?.startDate || null}
            vacationEndDate={user.vacation?.endDate || null}
            substituteUserIds={user.vacation?.substituteUserIds || []}
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
