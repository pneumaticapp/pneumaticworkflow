/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { PlayLogoIcon } from '../icons';
import { IntlMessages } from '../IntlMessages';

import styles from './Sidebar.css';

export interface IStartProcessButton {
  tabIndex?: number;
  onClick(): void;
}

export function StartProcessButton({ tabIndex, onClick }: IStartProcessButton) {
  return (
    <button tabIndex={tabIndex} className={classnames('active', styles['sidebar__start-button'])} onClick={onClick}>
      <PlayLogoIcon className={styles['start-button__icon']} />
      <p className={styles['start-button__text']}>
        <IntlMessages id="select-template.run-workflow" />
      </p>
    </button>
  );
}
