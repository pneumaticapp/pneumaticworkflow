import React, { useEffect, useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { EmailInvitesTab } from './tabs/EmailInvitesTab';
import { OAuthInvitesTab } from './tabs/OAuthInvitesTab';
import { useDelayUnmount } from '../../hooks/useDelayUnmount';
import { InvitesType } from '../../types/team';
import { ITeamInvitesPopupProps } from './types';
import { Header, SideModal } from '../UI';
import { IntlMessages } from '../IntlMessages';
import { isEnvGoogleAuth, isEnvMsAuth } from '../../constants/enviroment';

import styles from './TeamInvitesPopup.css';



export function TeamInvitesPopup({
  children,
  isTeamInvitesOpened,
  teamUsers,
  invitesUsersList,
  closeTeamInvitesPopup,
}: ITeamInvitesPopupProps) {
  const { formatMessage } = useIntl();
  const [activeTab, setActiveTab] = useState(InvitesType.Email);

  useEffect(() => {
    if (filteredTabsList.length > 0) {
      setActiveTab(filteredTabsList[0]);
    }
  }, [invitesUsersList]);

  const tabsListMap = useMemo(() => ({
    [InvitesType.Google]: {
      label: formatMessage({ id: 'team.modal-google-tab' }),
      isActive: activeTab === InvitesType.Google,
      content: <OAuthInvitesTab 
        type={InvitesType.Google} 
        users={invitesUsersList.filter((user) => user.source === InvitesType.Google)} 
        teamUsers={teamUsers} />,
      isVisible: isEnvGoogleAuth && invitesUsersList.some((user) => user.source === InvitesType.Google),
    },
    [InvitesType.Microsoft]: {
      label: formatMessage({ id: 'team.modal-microsoft-tab' }),
      isActive: activeTab === InvitesType.Microsoft,
      content: <OAuthInvitesTab 
        type={InvitesType.Microsoft} 
        users={invitesUsersList.filter((user) => user.source === InvitesType.Microsoft)} 
        teamUsers={teamUsers}
      />,
      isVisible: isEnvMsAuth && invitesUsersList.some((user) => user.source === InvitesType.Microsoft),
    },
    [InvitesType.Email]: {
      label: formatMessage({ id: 'team.modal-email-tab' }),
      content: <EmailInvitesTab />,
      isActive: activeTab === InvitesType.Email,
      isVisible: true,
    },
  }), [formatMessage, activeTab, invitesUsersList, teamUsers]);

  const filteredTabsList = useMemo(() => {
    return Object.values(InvitesType).filter((tabName) => tabsListMap[tabName].isVisible);
  }, [tabsListMap]);

  const renderTabsLabels = () => {
    const tabs = filteredTabsList.map((tabName: InvitesType) => {
      const { label, isActive } = tabsListMap[tabName];

      return (
        <button
          key={tabName}
          type="button"
          className={classnames('tab-button tab-button_yellow', isActive && 'tab-button_active', styles['tab'])}
          onClick={() => setActiveTab(tabName)}
        >
          {label}
        </button>
      );
    });

    return <div className={styles['tabs']}>{tabs}</div>;
  };

  const renderTabsContents = () => {
    const tabsContents = filteredTabsList.map((tabName) => {
      const { content, isActive } = tabsListMap[tabName];

      return (
        <div key={tabName} className={classnames(styles['tab-content'], isActive && styles['tab-content_active'])}>
          {content}
        </div>
      );
    });

    return <div className={styles['tabs-contents']}>{tabsContents}</div>;
  };

  // Waits for the end of the component hiding animation
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
