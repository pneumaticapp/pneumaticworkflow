/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import styles from './FeedItem.css';

interface IEllipsisProps {
  expand(): void;
}

export function Ellipsis({ expand }: IEllipsisProps) {
  const { messages } = useIntl();

  return (
    <a onClick={expand} className={styles['show-more']}>
      <span className={styles['show-more__text']}>
        {messages['general.show-more']}
      </span>
    </a>
  );
}
