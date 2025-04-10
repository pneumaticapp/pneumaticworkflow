import * as React from 'react';
import { useSelector } from 'react-redux';

import { UserData } from '../UserData/container';
import { IUserDataWithGroupProps } from './types';
import { IApplicationState } from '../../types/redux';
import { ETemplateOwnerType } from '../../types/template';

const UserDataWithGroup: React.FC<IUserDataWithGroupProps> = ({ type, idItem, children }) => {
  const groups = useSelector((state: IApplicationState) => state.groups.list);

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
