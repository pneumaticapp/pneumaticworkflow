/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { TopNavContainer } from '../../components/TopNav';
import { IntegrationsCommonContainer } from '../../components/IntegrationsCommon';

import styles from './IntegrationsLayout.css';

export class IntegrationsLayout extends React.Component {
  public render() {
    return (
      <>
        <TopNavContainer />
        <main>
          <div className="container-fluid">
            <div className={styles['container']}>
              <div className={styles['common']}>
                <IntegrationsCommonContainer />
              </div>

              <div className={styles['content']}>
                {this.props.children}
              </div>
            </div>
          </div>
        </main>
      </>
    );
  }
}
