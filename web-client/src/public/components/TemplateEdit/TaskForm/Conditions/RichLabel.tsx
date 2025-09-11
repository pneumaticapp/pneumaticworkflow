import React from 'react';
import classnames from 'classnames';
import { TooltipRichContent } from '../../TooltipRichContent';
import { Tooltip } from '../../../UI';
import { TTaskVariable } from '../../types';
import styles from './Conditions.css';

interface IRichLabelProps {
  variables: TTaskVariable[];
  variable: TTaskVariable;
  isSelected?: boolean;
  isFromStartingOrder?: boolean;
}

export function RichLabel({
  variable: { title, subtitle, richSubtitle },
  variables,
  isSelected,
  isFromStartingOrder,
}: IRichLabelProps) {
  return (
    <Tooltip
      interactive={false}
      containerClassName={styles['condition__tooltop']}
      content={
        <TooltipRichContent
          title={title}
          subtitle={isFromStartingOrder ? title || '' : subtitle || ''}
          variables={variables}
          hideTitle={isFromStartingOrder}
        />
      }
    >
      <div className={classnames(styles['rich-label'], isSelected && styles['condition__dropdown-option-is-selected'])}>
        {isFromStartingOrder ? (
          richSubtitle || title
        ) : (
          <>
            <div className={styles['variable-title']}>{title}</div>
            <div className={styles['variable-richsubtitle']}>{richSubtitle}</div>
          </>
        )}
      </div>
    </Tooltip>
  );
}
