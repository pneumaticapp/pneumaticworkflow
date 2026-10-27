import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';
import { getUserPendingActions } from '../../../redux/selectors/user';
import { EPlanActions } from '../../../utils/getPlanPendingActions';

import styles from './InfoWarningsModal.css';

export interface IInfoWarningProps {
  onClickActionButton?(): void;
}

export function PremiumFeaturesWarning() {
  const { formatMessage } = useIntl();
  const pendingActions = useSelector(getUserPendingActions);

  const actionsMap = {
    [EPlanActions.Upgrade]: null,
    [EPlanActions.ChoosePlan]: null,
  };
  return (
    <>
      <p className={styles['warning-title']}>{formatMessage({ id: 'template.warning-premium-feature-title' })}</p>
      <p className={styles['warning-description']}>{formatMessage({ id: 'template.warning-premium-feature-desc' })}</p>
      <ul className={styles['warning-list']}>
        {pendingActions.map((action) => {
          const button = actionsMap[action];
          if (!button) {
            return null;
          }

          return (
            <li key={action} className={styles['warning-item']}>
              {button}
            </li>
          );
        })}
      </ul>
    </>
  );
}
