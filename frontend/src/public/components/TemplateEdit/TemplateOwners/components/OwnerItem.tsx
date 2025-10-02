import React, { FC } from 'react';
import { useIntl } from 'react-intl';

import { Avatar, TAvatarUser } from '../../../UI';
import { DeleteIcon } from '../../../icons';
import { TUserListItem } from '../../../../types/user';
import { ETemplateOwnerType } from '../../../../types/template';

import styles from './OwnerItem.css';

interface IOwnerItem {
  user: TUserListItem;
  name: string;
  removeOwner(): void;
}

const OwnerItem: FC<IOwnerItem> = ({ user, name, removeOwner }) => {
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
              ? formatMessage({ id: 'template.owner-admin' })
              : formatMessage({ id: 'template.owner-starter' })}
          </span>
        )}
      </div>
      <DeleteIcon onClick={removeOwner} className={styles['user-delete']} />
    </div>
  );
};

export default OwnerItem;
