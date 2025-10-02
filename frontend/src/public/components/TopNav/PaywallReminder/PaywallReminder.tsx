import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EPlanActions } from '../../../utils/getPlanPendingActions';
import { EPaywallReminderType } from '../utils/getPaywallType';

import styles from '../TopNav.css';

export interface IPaywallReminderProps {
  type: EPaywallReminderType;
  pendingActions: EPlanActions[];
}

export function PaywallReminder({ type, pendingActions }: IPaywallReminderProps) {
  const { formatMessage } = useIntl();

  const renderTitle = () => {
    const titleMap = {
      [EPaywallReminderType.Blocked]: 'paywall.users-limit',
      [EPaywallReminderType.Free]: 'paywall.free-plan',
    };

    return <span>{formatMessage({ id: titleMap[type] })}</span>;
  };

  const renderActions = () => {
    const actionsMap = {
      [EPlanActions.Upgrade]: null,
      [EPlanActions.ChoosePlan]: null,
    };

    const actions = pendingActions
      .map((action) => actionsMap[action])
      .filter(Boolean)
      .map((item, index) => (index === 0 ? item : [' or ', item]));

    return <span>{actions}</span>;
  };

  return (
    <div className={classnames(styles['top-bar'], styles[type])}>
      {renderTitle()}
      {renderActions()}
    </div>
  );
}
