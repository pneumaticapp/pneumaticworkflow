/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { RouteComponentProps } from 'react-router-dom';

import styles from './Auth.css';
import { Button } from 'reactstrap';
import { IntlMessages } from '../IntlMessages';

export interface IAuthUserProps {
  email?: string;
  logout(): void;
}

export type TAuthUserProps = IAuthUserProps & RouteComponentProps;

export class Auth extends React.Component<TAuthUserProps> {
  public render() {
    const { email, logout } = this.props;
    if (!email) {
      return <div className="loading" />;
    }

    return (
      <div className={styles['container']}>
        <div className="d-flex flex-column justify-content-between align-items-center">
          <IntlMessages id="main.logged-in-as"/> {email}
          <Button
            color="primary"
            size="lg"
            onClick={logout}
          >
            <IntlMessages id="user.logout-button"/>
          </Button>
        </div>
      </div>
    );
  }
}
