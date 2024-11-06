import * as React from 'react';

import { ITemplateListItem } from '../../types/template';
import { SideModalCard } from '../UI/SideModalCard';

import styles from './SelectTemplateModal.css';

export interface IStartProcessModalItem extends ITemplateListItem {
  selectWorkflow(): void;
}

export function StartProcessModalItem({ name, description, selectWorkflow }: IStartProcessModalItem) {
  return (
    <SideModalCard className={styles['item-container']} onClick={selectWorkflow}>
      <SideModalCard.Title className={styles['item__title']}>{name}</SideModalCard.Title>

      {description && <SideModalCard.Body className={styles['item__body']}>{description}</SideModalCard.Body>}
    </SideModalCard>
  );
}
