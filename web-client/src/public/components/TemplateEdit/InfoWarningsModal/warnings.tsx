import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';
import { getUserPendingActions } from '../../../redux/selectors/user';
import { EPlanActions } from '../../../utils/getPlanPendingActions';

import styles from './InfoWarningsModal.css';

export interface IInfoWarningProps {
  onClickActionButton?(): void;
}

export function UnassignedTasksWarning() {
  const { formatMessage } = useIntl();

  const links = [
    {
      title: 'How to invite your team',
      url: 'https://support.pneumatic.app/en/articles/5579977-inviting-your-team-to-pneumatic',
    },
    {
      title: 'How to add free external users',
      url: 'https://support.pneumatic.app/en/articles/6145048-free-external-users',
    },
  ];

  return (
    <>
      <p className={styles['warning-title']}>
        {formatMessage({ id: 'template.warning-unassigned-perforemers-title' })}
      </p>
      <p className={styles['warning-description']}>
        {formatMessage({ id: 'template.warning-unassigned-perforemers-desc' })}
      </p>
      <ul className={styles['warning-list']}>
        {links.map(({ title, url }) => (
          <li className={styles['warning-item']}>
            <a href={url} target="_blank" className={styles['warning-link']} rel="noreferrer">
              {title}
            </a>
          </li>
        ))}
      </ul>
    </>
  );
}

export function PremiumFeaturesWarning() {
  const { formatMessage } = useIntl();
  const pendingActions = useSelector(getUserPendingActions);

  const actionsMap = {
    [EPlanActions.Upgrade]: null,
    [EPlanActions.ChoosePlan]: null,
  };
  const actionButtons = pendingActions.map((action) => actionsMap[action]).filter(Boolean);

  return (
    <>
      <p className={styles['warning-title']}>{formatMessage({ id: 'template.warning-premium-feature-title' })}</p>
      <p className={styles['warning-description']}>{formatMessage({ id: 'template.warning-premium-feature-desc' })}</p>
      <ul className={styles['warning-list']}>
        {actionButtons.map((button) => (
          <li className={styles['warning-item']}>{button}</li>
        ))}
      </ul>
    </>
  );
}
