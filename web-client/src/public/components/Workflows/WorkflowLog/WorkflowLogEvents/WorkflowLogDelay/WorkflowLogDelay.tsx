/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import * as classnames from 'classnames';

import { IWorkflowLogItem } from '../../../../../types/workflow';
import { getSnoozedUntilDate } from '../../../../../utils/dateTime';
import { Header } from '../../../../UI/Typeography/Header';
import { TWorkflowLogTheme } from '../../WorkflowLog';

import styles from './WorkflowLogDelay.css';

export interface IWorkflowLogDelayProps extends Pick<IWorkflowLogItem, 'delay'> {
  theme: TWorkflowLogTheme;
}

export function WorkflowLogDelay({ delay, theme }: IWorkflowLogDelayProps) {
  if (!delay) {
    return null;
  }

  const getThemeClassName = React.useCallback(() => {
    const themeClassNameMap: { [key in TWorkflowLogTheme]: string } = {
      beige: styles['container-beige'],
      white: styles['container-white'],
    };

    return themeClassNameMap[theme];
  }, [theme]);

  const { formatMessage } = useIntl();

  return (
    <div className={classnames(styles['container'], getThemeClassName())}>
      <Header size="6" tag="p" className={styles['text']}>
        {formatMessage({ id: 'task.log-delay' }, { date: getSnoozedUntilDate(delay) })}
      </Header>
    </div>
  );
}
