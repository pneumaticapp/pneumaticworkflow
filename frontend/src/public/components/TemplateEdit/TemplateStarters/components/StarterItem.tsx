import React, { FC } from 'react';
import { useIntl } from 'react-intl';

import { Avatar, TAvatarUser } from '../../../UI';
import { DeleteIcon } from '../../../icons';
import { TUserListItem } from '../../../../types/user';
import { ETemplateOwnerType } from '../../../../types/template';

import styles from './StarterItem.css';

interface IStarterItemProps {
  user: TUserListItem;
  name: string;
  onRemove(): void;
}

const StarterItem: FC<IStarterItemProps> = ({ user, name, onRemove }) => {
  const { formatMessage } = useIntl();
  const avatar: TAvatarUser = user || { type: ETemplateOwnerType.UserGroup };

  return (
    <div className={styles['user']}>
      <Avatar size="lg" user={avatar} />
      <div className={styles['user-info']}>
        <span className={styles['user-name']} title={name}>
          {name}
        </span>
        {user.type === ETemplateOwnerType.User && (
          <span className={styles['user-role']}>
            {user.isAdmin
              ? formatMessage({ id: 'template.user-admin' })
              : formatMessage({ id: 'template.user-role' })}
          </span>
        )}
      </div>
      <DeleteIcon onClick={onRemove} className={styles['user-delete']} />
    </div>
  );
};

export default StarterItem;