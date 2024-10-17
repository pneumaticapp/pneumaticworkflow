/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { TPlaceholderMood, IPlaceholderIconProps } from './types';

import { Header } from '..';

import styles from './Placeholder.css';

export interface IPlaceholderProps {
  mood?: TPlaceholderMood;
  Icon(props: IPlaceholderIconProps): JSX.Element;
  title: string;
  description?: string;
  footer?: React.ReactNode;
  containerClassName?: string;
}

export function Placeholder({
  mood = 'neutral',
  Icon,
  title,
  description,
  footer,
  containerClassName,
}: IPlaceholderProps) {
  return (
    <div
      className={classnames(
        styles['container'],
        containerClassName,
      )}
    >
      <div className={styles['icon']}>
        <Icon mood={mood} />
      </div>
      <Header tag="p" size="6" className={styles['title']}>{title}</Header>
      {description && <p className={styles['description']}>{description}</p>}
      {footer && <div className={styles['footer']}>{footer}</div>}
    </div>
  );
}
