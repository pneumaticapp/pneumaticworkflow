/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { IntlMessages } from '../IntlMessages';

import styles from './VerificationReminder.css';

export interface IVerificationReminderProps {
  isResendClicked: boolean;
  resendVerification(): void;
}

export const VerificationReminder = ({
  isResendClicked,
  resendVerification,
}: IVerificationReminderProps) => {
  const verificationReminderClassName = classnames(
    styles['verification-reminder'],
  );

  return (
    <p className={verificationReminderClassName}>
      {isResendClicked
        ? <IntlMessages id="dashboard.verification-hint-check-inbox" />
        : <>
          <IntlMessages id="dashboard.verification-hint-instructions-send" />
          <a className={styles['verification-reminder__link']} onClick={resendVerification}>
            <IntlMessages id="dashboard.verification-hint-resend-email" />
          </a>
        </>
      }
    </p>
  );
};
