/* eslint-disable no-restricted-syntax */
/* eslint-disable react/sort-comp */
import * as React from 'react';
import { matchPath } from 'react-router-dom';

import { DashboardWidgets } from '../../components/Dashboard/DashboardWidgets';
import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { ESettingsTabs } from '../../types/profile';
import { Tabs } from '../../components/UI';

import styles from './SettingsLayout.css';

export interface ISettingsLayoutComponentProps {
  children: React.ReactChild;
  activeTab: ESettingsTabs;
  onChangeTab(tab: ESettingsTabs): void;
}

export class SettingsLayoutComponent extends React.Component<ISettingsLayoutComponentProps> {
  public renderSettingsContent = () => {
    const { activeTab, onChangeTab } = this.props;

    return (
      <div className={styles['navbar-left__content']}>
        <Tabs
          values={[
            { id: ESettingsTabs.Profile, label: 'Profile' },
            { id: ESettingsTabs.AccountSettings, label: 'Settings' },
          ]}
          activeValueId={activeTab}
          onChange={onChangeTab}
        />
      </div>
    );
  };

  private mapLeftContent: { [key: string]: () => React.ReactNode } = {
    [ERoutes.Profile]: this.renderSettingsContent,
    [ERoutes.AccountSettings]: this.renderSettingsContent,
  };

  private get leftContent() {
    const { pathname } = history.location;
    for (const key of Object.keys(this.mapLeftContent)) {
      if (matchPath(pathname, key)) {
        return this.mapLeftContent[key]();
      }
    }

    return null;
  }

  public render() {
    const { children } = this.props;

    return (
      <>
        <TopNavContainer leftContent={this.leftContent} />
        <main>
          <div className="container-fluid">
            <div className={styles['container']}>
              <div className={styles['form-container']}>{children}</div>
              <div className={styles['widgets']}>
                <DashboardWidgets />
              </div>
            </div>
          </div>
        </main>
      </>
    );
  }
}
