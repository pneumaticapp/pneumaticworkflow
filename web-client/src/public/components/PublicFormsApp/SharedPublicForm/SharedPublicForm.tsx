import React from 'react';
import { NotificationContainer } from '../../UI/Notifications';
import { Copyright } from '../common/Copyright';
import { PublicForm } from '../common/PublicForm/PublicForm';

import styles from './SharedPublicForm.css';

export function SharedPublicForm() {
  return (
    <div className={styles['container']}>
      <NotificationContainer />
      <PublicForm type="shared" />
      <Copyright />
    </div>
  );
}
