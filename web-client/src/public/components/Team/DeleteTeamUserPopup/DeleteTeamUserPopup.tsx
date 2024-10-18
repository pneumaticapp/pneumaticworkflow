import { Modal, ModalBody, ModalFooter, ModalHeader } from 'reactstrap';
import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { IntlMessages } from '../../IntlMessages';
import { TDeclineIvitePayload, TDeleteUserPayload } from '../../../redux/actions';
import { EDeleteUserModalState } from '../../../types/redux';
import { TUserListItem } from '../../../types/user';
import { getDropdownUsersList, getUserFullName } from '../../../utils/users';
import { Loader } from '../../UI/Loader';
import { DropdownList } from '../../UI/DropdownList';
import { Button } from '../../UI';

import styles from './DeleteTeamUserPopup.css';

export interface IDeleteTeamUserPopupProps {
  user: TUserListItem | null;
  isUserActive: boolean;
  modalState: EDeleteUserModalState;
  userWorkflowsCount: number;
  usersList: TUserListItem[];
  closeModal(): void;
  deleteUser(params: TDeleteUserPayload): void;
  declineInvite(params: TDeclineIvitePayload): void;
}

export function DeleteTeamUserPopup({
  user,
  usersList,
  isUserActive,
  modalState,
  userWorkflowsCount,
  closeModal,
  deleteUser,
  declineInvite,
}: IDeleteTeamUserPopupProps) {
  if (!user) {
    return null;
  }

  const [reassignedUserId, setReassignedUserId] = React.useState<number | null>(null);
  const dropdownSelections = getDropdownUsersList(usersList).filter((dropdownUser) => dropdownUser.id !== user.id);
  const { email } = user;
  const { formatMessage } = useIntl();

  const inSubmitDisabled =
    modalState === EDeleteUserModalState.PerformingAction || (userWorkflowsCount > 0 && !reassignedUserId);

  const modalTitle = isUserActive ? 'team.delete-title' : 'team.delete-invite-title';

  const renderMessage = () => {
    const name = <span className={styles['message-text__emphasis']}>{getUserFullName(user) || email}</span>;

    if (userWorkflowsCount === 0) {
      const messageId = isUserActive ? 'team-delete-confirm' : 'team-delete-invite-confirm';

      return formatMessage({ id: messageId }, { name });
    }

    return formatMessage(
      { id: 'team-delete-with-reassing-confirm' },
      {
        name,
        workflowsCount: <span className={styles['message-text__emphasis']}>{userWorkflowsCount}</span>,
      },
    );
  };

  const handlePerformAction = () => {
    if (isUserActive && user.id) {
      deleteUser({ userId: user.id, reassignedUserId });

      return;
    }

    if (user.invite?.id && user.id) {
      declineInvite({
        userId: user.id,
        inviteId: user.invite?.id,
        reassignedUserId,
      });
    }
  };

  const handleCloseModal = () => {
    setReassignedUserId(null);
    closeModal();
  };

  const renderContent = () => {
    if (modalState === EDeleteUserModalState.FetchingUserData) {
      return (
        <>
          <ModalHeader toggle={handleCloseModal} className={styles['header']} />
          <Loader isLoading />
        </>
      );
    }

    return (
      <>
        <ModalHeader toggle={handleCloseModal} className={styles['header']}>
          <IntlMessages id={modalTitle} tagName="p" />
        </ModalHeader>
        <ModalBody className={styles['body']}>
          <p className={styles['message-text']}>{renderMessage()}</p>

          {userWorkflowsCount > 0 && (
            <div className={styles['dropdown']}>
              <DropdownList
                options={dropdownSelections}
                onChange={(value) => setReassignedUserId(value.id!)}
                placeholder={formatMessage({ id: 'team.select-reassigned-user' })}
                isSearchable
              />
            </div>
          )}
        </ModalBody>
        <ModalFooter className={styles['footer']}>
          <div
            className={classnames(styles['popup-buttons'], {
              [styles['submit_loading']]: modalState === EDeleteUserModalState.PerformingAction,
            })}
          >
            <Button
              label={formatMessage({ id: 'team.delete-submit' })}
              className={styles['popup-button_submit']}
              buttonStyle="yellow"
              isLoading={modalState === EDeleteUserModalState.PerformingAction}
              onClick={handlePerformAction}
              disabled={inSubmitDisabled}
            />
            <button
              type="button"
              aria-label="button"
              className="cancel-button"
              id="team-dropdown-modal-footer-cancel-button"
              onClick={handleCloseModal}
              disabled={modalState === EDeleteUserModalState.PerformingAction}
            >
              <IntlMessages id="team.delete-cancel" />
            </button>
          </div>
        </ModalFooter>
      </>
    );
  };

  return (
    <Modal
      isOpen={modalState !== EDeleteUserModalState.Closed}
      toggle={handleCloseModal}
      centered
      wrapClassName={classnames(
        styles['team-popup'],
        modalState === EDeleteUserModalState.FetchingUserData && styles['team-popup__loading'],
      )}
    >
      {renderContent()}
    </Modal>
  );
}
