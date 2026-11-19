import React from 'react';
import { useSelector } from 'react-redux';

import { UserData } from '../UserData/container';
import type { IUserDataWithGroupProps } from './types';
import type { RootState } from '../../redux/store';
import { ETemplateOwnerType } from '../../types/template';

const UserDataWithGroup: React.FC<IUserDataWithGroupProps> = ({ type, idItem, children }) => {
  const groups = useSelector((state: RootState) => state.groups.list);

  if (type === ETemplateOwnerType.UserGroup) {
    const currentGroup = groups.find(({ id }) => id === idItem);
    if (!currentGroup) return null;
    const groupAvatar = {
      type: ETemplateOwnerType.UserGroup,
      firstName: currentGroup.name,
    };

    return <>{children(groupAvatar)}</>;
  }

  return (
    <UserData userId={idItem}>
      {(user) => {
        if (!user) return null;

        return <>{children(user)}</>;
      }}
    </UserData>
  );
};

export default UserDataWithGroup;
