/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { matchPath } from 'react-router-dom';
import { IntlShape } from 'react-intl';

import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { UserListSortingContainer } from './UserListSortingContainer';

import styles from './TeamLayout.css';

type TTeamLayoutComponentProps = {
  intl: IntlShape;
};

export class TeamLayoutComponent extends React.Component<TTeamLayoutComponentProps> {
  public renderTeamLeftContent = () => {
    return (
      <div className={styles['navbar-left__content']}>
        <UserListSortingContainer />
      </div>
    );
  };

  private mapLeftContent: { [key: string]: () => React.ReactNode } = {
    [ERoutes.Team]: this.renderTeamLeftContent,
  };

  private get leftContent() {
    const { pathname } = history.location;
    for (let key of Object.keys(this.mapLeftContent)) {
      if (matchPath(pathname, key)) {
        return this.mapLeftContent[key]();
      }
    }

    return null;
  }

  public render() {
    return (
      <>
        <TopNavContainer leftContent={this.leftContent} />
        <main>
          <div className="container-fluid">
            {this.props.children}
          </div>
        </main>
      </>
    );
  }
}
