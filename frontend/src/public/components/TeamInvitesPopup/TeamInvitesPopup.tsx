import React, { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { EmailInvitesTab } from './tabs/EmailInvitesTab';
import { OAuthInvitesTab } from './tabs/OAuthInvitesTab';

import { useDelayUnmount } from '../../hooks/useDelayUnmount';
import { EInvitesType, IOAuthInviteView, IUserInviteMicrosoft } from '../../types/team';
import { TUserListItem } from '../../types/user';
import { Header, SideModal } from '../UI';
import { IntlMessages } from '../IntlMessages';
import { NotificationManager } from '../UI/Notifications';
import { getGoogleErrorMessage } from '../../utils/google/getGoogleErrorMessage';
import { connectGoogle, isArrayWithItems } from '../../utils/helpers';
import { MicrosoftInvitesTab } from './tabs/MicrosoftInvitesTab';

import styles from './TeamInvitesPopup.css';
import { isEnvGoogleAuth, isEnvMsAuth } from '../../constants/enviroment';

export interface ITeamInvitesPopupProps {
  children?: any,
  isTeamInvitesOpened: boolean;
  currentUserEmail: string;
  googleUsers: IOAuthInviteView[];
  microsoftUsers: IUserInviteMicrosoft[];
  teamUsers: TUserListItem[];
  tabByDefault?: EInvitesType;
  closeTeamInvitesPopup(): void;
  changeGoogleInvites(data: IOAuthInviteView[]): void;
}

export function TeamInvitesPopup({
  children,
  googleUsers,
  microsoftUsers,
  isTeamInvitesOpened,
  currentUserEmail,
  teamUsers,
  tabByDefault,
  changeGoogleInvites,
  closeTeamInvitesPopup,
}: ITeamInvitesPopupProps) {
  const { formatMessage } = useIntl();

  const [activeTab, setActiveTab] = useState(EInvitesType.Email);

  useEffect(() => {
    window.addEventListener('message', handleReceivingOAuthUsers, false);

    return () => {
      window.removeEventListener('message', handleReceivingOAuthUsers, false);
    };
  }, []);

  useEffect(() => {
    if (tabByDefault) {
      setActiveTab(tabByDefault);

      const defaultActionMap = {
        [EInvitesType.Email]: () => {},
        [EInvitesType.Google]: connectGoogle,
        [EInvitesType.Microsoft]: () => {},
      };

      defaultActionMap[tabByDefault]();
    }
  }, [tabByDefault]);

  const handleReceivingOAuthUsers = async (event: WindowEventMap['message']) => {
    if (!event.data) {
      return;
    }

    const { googleUsers: googleUser, errors } = event.data;

    if (errors) {
      const errorMessages = Array.isArray(errors) ? errors : [];
      errorMessages.forEach((error) => {
        const errorMessage = getGoogleErrorMessage(new Error(error.message));

        NotificationManager.warning({ message: errorMessage });
      });

      return;
    }

    const handlingOAuthParamsMap = [
      {
        check: () => isArrayWithItems(googleUser),
        params: {
          type: 'google',
          users: googleUser,
          setUsers: changeGoogleInvites,
        },
      },
    ];

    const handlingParams = handlingOAuthParamsMap.find(({ check }) => check())?.params;
    if (!handlingParams) {
      return;
    }

    const { type, users, setUsers } = handlingParams;
    const normalizedUsers = (users as IOAuthInviteView[])
      .filter(({ email }) => email !== currentUserEmail)
      .map((user) => ({
        ...user,
        type: type as IOAuthInviteView['type'],
      }));

    setUsers(normalizedUsers);
  };

  const renderTabsLabels = () => {
    const tabs = Object.values(EInvitesType).map((tabName) => {
      const isActive = activeTab === tabName;

      const tabLabelsMap = {
        [EInvitesType.Email]: formatMessage({ id: 'team.modal-email-tab' }),
        [EInvitesType.Google]: formatMessage({ id: 'team.modal-google-tab' }),
        [EInvitesType.Microsoft]: formatMessage({ id: 'team.modal-microsoft-tab' }),
      };

      if (!isEnvGoogleAuth && tabName === EInvitesType.Google) {
        return false;
      }

      if (!isEnvMsAuth && !microsoftUsers.length && tabName === EInvitesType.Microsoft) {
        return false;
      }

      return (
        <button
          key={tabName}
          type="button"
          className={classnames('tab-button tab-button_yellow', isActive && 'tab-button_active', styles['tab'])}
          onClick={() => setActiveTab(tabName)}
        >
          {tabLabelsMap[tabName]}
        </button>
      );
    });

    return <div className={styles['tabs']}>{tabs}</div>;
  };

  const renderTabsContents = () => {
    const tabsContents = Object.values(EInvitesType).map((tabName) => {
      const isActive = activeTab === tabName;

      const tabContentsMap = {
        [EInvitesType.Google]: <OAuthInvitesTab type="google" users={googleUsers} teamUsers={teamUsers} />,
        [EInvitesType.Microsoft]: <MicrosoftInvitesTab type="microsoft" users={microsoftUsers} teamUsers={teamUsers} />,
        [EInvitesType.Email]: <EmailInvitesTab />,
      };

      if (!isEnvGoogleAuth && tabName === EInvitesType.Google) {
        return false;
      }

      if (!isEnvMsAuth && !microsoftUsers.length && tabName === EInvitesType.Microsoft) {
        return false;
      }

      return (
        <div key={tabName} className={classnames(styles['tab-content'], isActive && styles['tab-content_active'])}>
          {tabContentsMap[tabName]}
        </div>
      );
    });

    return <div className={styles['tabs-contents']}>{tabsContents}</div>;
  };

  const shouldRender = useDelayUnmount(isTeamInvitesOpened, 150);
  if (!shouldRender) {
    return null;
  }

  return (
    <SideModal onClose={closeTeamInvitesPopup} isClosing={!isTeamInvitesOpened}>
      <SideModal.Header className={styles['header']}>{renderTabsLabels()}</SideModal.Header>

      <SideModal.Body>
        <Header tag="span" size="6" className={styles['title']}>
          <IntlMessages id="team.modal-header-title">{children}</IntlMessages>
        </Header>

        {renderTabsContents()}
      </SideModal.Body>
    </SideModal>
  );
}
