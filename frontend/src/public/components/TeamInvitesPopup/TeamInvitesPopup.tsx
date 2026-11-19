import React, { useEffect, useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { EmailInvitesTab } from './tabs/EmailInvitesTab';
import { OAuthInvitesTab } from './tabs/OAuthInvitesTab';
import { useDelayUnmount } from '../../hooks/useDelayUnmount';
import { EInvitesType } from '../../types/team';
import type { ITeamInvitesPopupProps } from './types';
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
  const [activeTab, setActiveTab] = useState(EInvitesType.Email);

  useEffect(() => {
    if (filteredTabsList.length > 0) {
      setActiveTab(filteredTabsList[0]);
    }
  }, [invitesUsersList]);

  const tabsListMap = useMemo(
    () => ({
      [EInvitesType.Google]: {
        label: formatMessage({ id: 'team.modal-google-tab' }),
        isActive: activeTab === EInvitesType.Google,
        content: (
          <OAuthInvitesTab
            type={EInvitesType.Google}
            users={invitesUsersList.filter((user) => user.source === EInvitesType.Google)}
            teamUsers={teamUsers}
          />
        ),
        isVisible: isEnvGoogleAuth && invitesUsersList.some((user) => user.source === EInvitesType.Google),
      },
      [EInvitesType.Microsoft]: {
        label: formatMessage({ id: 'team.modal-microsoft-tab' }),
        isActive: activeTab === EInvitesType.Microsoft,
        content: (
          <OAuthInvitesTab
            type={EInvitesType.Microsoft}
            users={invitesUsersList.filter((user) => user.source === EInvitesType.Microsoft)}
            teamUsers={teamUsers}
          />
        ),
        isVisible: isEnvMsAuth && invitesUsersList.some((user) => user.source === EInvitesType.Microsoft),
      },
      [EInvitesType.Email]: {
        label: formatMessage({ id: 'team.modal-email-tab' }),
        content: <EmailInvitesTab />,
        isActive: activeTab === EInvitesType.Email,
        isVisible: true,
      },
    }),
    [formatMessage, activeTab, invitesUsersList, teamUsers],
  );

  const filteredTabsList = useMemo(() => {
    return Object.values(EInvitesType).filter((tabName) => tabsListMap[tabName].isVisible);
  }, [tabsListMap]);

  const renderTabsLabels = () => {
    const tabs = filteredTabsList.map((tabName: EInvitesType) => {
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
