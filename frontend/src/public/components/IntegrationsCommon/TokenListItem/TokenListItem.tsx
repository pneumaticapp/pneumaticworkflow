import React from 'react';

import { Button } from '../../UI/Buttons/Button';
import { Tooltip } from '../../UI/Tooltip';
import type { ITokenListItemProps } from './types';

import styles from './TokenListItem.css';

const TOKEN_MASK = '••••••••';

export function TokenListItem({
  name,
  tokenPrefix,
  details,
  meta,
  action: { label, onClick, isDisabled, tooltip, 'data-testid': actionTestId },
  'data-testid': testId,
}: ITokenListItemProps) {
  return (
    <li className={styles['token-list__item']} data-testid={testId}>
      <div className={styles['token-list__info']}>
        <h3 className={styles['token-list__name']}>{name}</h3>
        {details && <p className={styles['token-list__details']}>{details}</p>}
        <code className={styles['token-list__token']}>
          {tokenPrefix}
          {TOKEN_MASK}
        </code>
        {meta && <p className={styles['token-list__meta']}>{meta}</p>}
      </div>
      <div className={styles['token-list__actions']}>
        <Tooltip disabled={!tooltip} content={tooltip}>
          <div>
            <Button
              type="button"
              className={styles['token-list__action']}
              onClick={onClick}
              size="sm"
              buttonStyle="transparent-black"
              disabled={isDisabled}
              label={label}
              data-testid={actionTestId}
            />
          </div>
        </Tooltip>
      </div>
    </li>
  );
}
