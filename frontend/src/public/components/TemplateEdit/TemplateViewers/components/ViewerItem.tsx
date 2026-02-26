import React, { FC } from 'react';
import { useIntl } from 'react-intl';

import { Avatar, TAvatarUser } from '../../../UI';
import { DeleteIcon } from '../../../icons';
import { TUserListItem } from '../../../../types/user';
import { ETemplateOwnerType } from '../../../../types/template';
import { IGroup } from '../../../../redux/team/types';

import styles from './ViewerItem.css';

interface IViewerItemProps {
  userData?: TUserListItem;
  groupData?: IGroup;
  onRemove(params: { id: number }): void;
}

const ViewerItem: FC<IViewerItemProps> = ({ userData, groupData, onRemove }) => {
  const { formatMessage } = useIntl();
  
  const isGroup = !!groupData;
  const user = userData || groupData;
  const name = isGroup ? groupData!.name : `${userData!.firstName} ${userData!.lastName}`.trim() || userData!.email;
  
  const avatar: TAvatarUser = isGroup 
    ? { type: ETemplateOwnerType.UserGroup, firstName: groupData!.name }
    : userData || { type: ETemplateOwnerType.UserGroup };

  const handleRemove = () => {
    onRemove({ id: user!.id });
  };

  return (
    <div className={styles['user']}>
      <Avatar size="lg" user={avatar} />
      <div className={styles['user-info']}>
        <span className={styles['user-name']} title={name}>
          {name}
        </span>
        {userData && (
          <span className={styles['user-role']}>
            {formatMessage({ id: 'template.viewer-role' })}
          </span>
        )}
        {groupData && (
          <span className={styles['user-role']}>
            {formatMessage({ id: 'template.viewer-group-role' })}
          </span>
        )}
      </div>
      <DeleteIcon onClick={handleRemove} className={styles['user-delete']} />
    </div>
  );
};

export default ViewerItem;