import React, { memo } from 'react';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { PlayLogoIcon } from '../icons';
import { IntlMessages } from '../IntlMessages';
import { getTemplatesStore } from '../../redux/selectors/templates';
import { getCanAccessWorkflows } from '../../redux/selectors/user';

import styles from './Sidebar.css';

export interface IStartProcessButton {
  tabIndex?: number;
  onClick(): void;
}

export const StartProcessButton = memo(function ({ tabIndex, onClick }: IStartProcessButton) {
  const canAccessWorkflows = useSelector(getCanAccessWorkflows);
  const { isTemplateOwner } = useSelector(getTemplatesStore);

  if (!canAccessWorkflows && !isTemplateOwner) {
    return null;
  }

  return (
    <button
      type="button"
      tabIndex={tabIndex}
      className={classnames('active', styles['sidebar__start-button'])}
      onClick={onClick}
      aria-label="Run workflow"
    >
      <PlayLogoIcon className={styles['start-button__icon']} />
      <p className={styles['start-button__text']}>
        <IntlMessages id="select-template.run-workflow" />
      </p>
    </button>
  );
});
