import React from 'react';
import { getFormattedSubtitle } from '../TaskForm/utils/getFormattedSubtitle';
import { TTaskVariable } from '../types';
import styles from './TooltipRichContent.css';

interface ITooltipRichContentProps {
  title: string;
  subtitle: string;
  variables: TTaskVariable[];
}

export function TooltipRichContent({ title, subtitle, variables }: ITooltipRichContentProps) {
  const formattedSubtitle = getFormattedSubtitle(subtitle, variables);

  return (
    <div className={styles['tooltip-rich-content__box']}>
      <div className={styles['tooltip-rich-content__title']}>{title}</div>
      <div
        className={styles['tooltip-rich-content__subtitle']}
        dangerouslySetInnerHTML={{ __html: formattedSubtitle }}
      />
    </div>
  );
}
