import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { loadGroups } from '../../redux/actions';
import { usersFetchStarted } from '../../redux/accounts/slice';
import { getBrowserConfig } from '../../utils/getConfig';
import TaskDetailContainer from '../TaskDetail';
import { ETaskCardViewMode } from '../TaskCard';
import { useWhiteBackground } from '../../hooks/useWhiteBackground';

import styles from './GuestTask.css';

export function GuestTask() {
  const {
    config: { mainPage },
  } = getBrowserConfig();
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  useWhiteBackground();

  React.useEffect(() => {
    dispatch(usersFetchStarted());
    dispatch(loadGroups());
  }, []);

  return (
    <div className={styles['container']}>
      <TaskDetailContainer viewMode={ETaskCardViewMode.Guest} />

      <p className={styles['copyright']}>
        {formatMessage(
          { id: 'public-form.copyright' },
          {
            link: (
              <a className={styles['copyright__link']} href={mainPage} target="_blank" rel="noreferrer">
                {formatMessage({ id: 'public-form.pneumatic' })}
              </a>
            ),
          },
        )}
      </p>
    </div>
  );
}
