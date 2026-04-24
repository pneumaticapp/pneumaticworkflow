import React from 'react';
import { useIntl } from 'react-intl';
import { getFormattedSubtitleSegments } from '../TaskForm/utils/getFormattedSubtitle';
import { TTaskVariable } from '../types';
import styles from './TooltipRichContent.css';

interface ITooltipRichContentProps {
  title: string;
  subtitle: string;
  variables: TTaskVariable[];
  hideTitle?: boolean;
}

export function TooltipRichContent({ title, subtitle, variables, hideTitle }: ITooltipRichContentProps) {
  const { formatMessage } = useIntl();
  const segments = getFormattedSubtitleSegments(subtitle, variables, formatMessage);

  return (
    <div className={styles['tooltip-rich-content__box']}>
      {!hideTitle && <div className={styles['tooltip-rich-content__title']}>{title}</div>}
      <div className={styles['tooltip-rich-content__subtitle']}>
        {segments.map((seg) =>
          seg.type === 'text' ? (
            <React.Fragment key={seg.id}>{seg.value}</React.Fragment>
          ) : (
            <span key={seg.id}>{seg.title}</span>
          ),
        )}
      </div>
    </div>
  );
}
