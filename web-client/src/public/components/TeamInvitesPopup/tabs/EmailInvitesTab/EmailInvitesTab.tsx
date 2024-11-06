import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';
import * as PerfectScrollbar from 'react-perfect-scrollbar';

import { inviteUsers } from '../../../../redux/actions';
import { createUniqueId } from '../../../../utils/createId';
import { isArrayWithItems } from '../../../../utils/helpers';
import { validateInviteEmail } from '../../../../utils/validators';
import { SuccessCheckIcon, ErrorBlockIcon } from '../../../icons';
import { Button, InputField, Loader } from '../../../UI';

import styles from './EmailInvitesTab.css';
import popupStyles from '../../TeamInvitesPopup.css';

type TUploadingInviteStatus = 'initial' | 'uploading' | 'success' | 'error';
type TUploadingInvite = {
  id: string;
  email: string;
  status: TUploadingInviteStatus;
};

const ScrollBar = PerfectScrollbar as unknown as Function;

export function EmailInvitesTab() {
  const dispatch = useDispatch();
  const { useState } = React;
  const { formatMessage } = useIntl();
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState('');
  const [invites, setInvites] = useState<TUploadingInvite[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addInvite = React.useCallback<React.FormEventHandler<HTMLFormElement>>(
    (event) => {
      event.preventDefault();

      if (isLoading) {
        return;
      }

      const currentError = validateInviteEmail(inputValue);
      if (currentError) {
        setError(currentError);

        return;
      }
      const newInviteId = createUniqueId('xxxyxx');
      const newInvite: TUploadingInvite = {
        id: newInviteId,
        email: inputValue,
        status: 'initial',
      };
      setInvites([...invites, newInvite]);
      setInputValue('');
      dispatch(
        inviteUsers({
          invites: [{ email: newInvite.email, type: 'email' }],
          withSuccessNotification: true,
          onStartUploading: () => {
            setIsLoading(true);
            changeInviteStatus(newInviteId, 'uploading');
          },
          onEndUploading: () => {
            setIsLoading(false);
            changeInviteStatus(newInviteId, 'success');
          },
          onError: () => {
            setIsLoading(false);
            changeInviteStatus(newInviteId, 'error');
          },
        }),
      );
    },
    [inputValue, setError],
  );

  const changeInviteStatus = (inviteId: string, newStatus: TUploadingInviteStatus) => {
    setInvites((prevInvites) => {
      const newInvites = prevInvites.map((invite) =>
        invite.id === inviteId ? { ...invite, status: newStatus } : invite,
      );

      return newInvites;
    });
  };

  const handleChange = (e: React.FormEvent<HTMLInputElement>) => {
    setError('');
    setInputValue(e.currentTarget.value);
  };

  const renderInviteStatus = (invite: TUploadingInvite) => {
    const inviteStatusMap = {
      initial: null,
      uploading: <Loader isLoading isCentered={false} containerClassName={styles['loader']} />,
      success: <SuccessCheckIcon />,
      error: <ErrorBlockIcon />,
    };

    return inviteStatusMap[invite.status];
  };

  return (
    <>
      <form onSubmit={addInvite} className={styles['form']} data-autofocus-first-field>
        <InputField
          autoFocus
          value={inputValue}
          onChange={handleChange}
          errorMessage={error}
          placeholder={formatMessage({ id: 'team.add-email-placeholder' })}
          fieldSize="md"
          className={popupStyles['input-field']}
        />
        <Button
          type="submit"
          label={formatMessage({ id: 'team.add-button' })}
          buttonStyle="yellow"
          size="md"
          className={styles['add-btn']}
          disabled={isLoading}
        />
      </form>

      {isArrayWithItems(invites) && (
        <ScrollBar options={{ suppressScrollX: true, wheelPropagation: false }} className={styles['scrollbar']}>
          <div className={styles['invites']}>
            {invites.map((invite) => {
              return (
                <div className={styles['invite']} key={invite.id}>
                  <span className={styles['invite__email']}>{invite.email}</span>
                  <span className={styles['invite__status']}>{renderInviteStatus(invite)}</span>
                </div>
              );
            })}
          </div>
        </ScrollBar>
      )}
    </>
  );
}
