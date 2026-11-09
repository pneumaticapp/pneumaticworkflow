import React from 'react';
import classnames from 'classnames';

import { IntlMessages } from '../../../components/IntlMessages';
import { Header } from '../../../components/UI';
import { useDocumentTitle } from '../../../hooks/useDocumentTitle';

import styles from '../User.css';

export function ExpiredInvite() {
  useDocumentTitle('ExpiredInvite');

  return (
    <>
      <Header size="4" tag="p" className={classnames('mb-5', styles['title'])}>
        <IntlMessages id="user.expired-invite-title" />
      </Header>
      <div className={classnames('text text-center mb-4', styles['text'])}>
        <IntlMessages id="user.expired-invite-description" />
      </div>
    </>
  );
}
