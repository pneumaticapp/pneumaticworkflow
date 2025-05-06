/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { PlayLogoIcon } from '../icons';
import { IntlMessages } from '../IntlMessages';
import { getTemplatesStore } from '../../redux/selectors/templates';

import styles from './Sidebar.css';
import { getIsAdmin } from '../../redux/selectors/user';

export interface IStartProcessButton {
  tabIndex?: number;
  onClick(): void;
}

export const StartProcessButton = React.memo(function ({ tabIndex, onClick }: IStartProcessButton) {
  const isAdmin = useSelector(getIsAdmin);
  if (!isAdmin) {
    const { isTemplateOwner } = useSelector(getTemplatesStore);
    if (!isTemplateOwner) return null;
  }

  return (
    <button tabIndex={tabIndex} className={classnames('active', styles['sidebar__start-button'])} onClick={onClick}>
      <PlayLogoIcon className={styles['start-button__icon']} />
      <p className={styles['start-button__text']}>
        <IntlMessages id="select-template.run-workflow" />
      </p>
    </button>
  );
});
