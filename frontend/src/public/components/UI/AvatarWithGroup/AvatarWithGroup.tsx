import * as React from 'react';

import { Avatar, IAvatarProps, TAvatarUser } from '../Avatar/Avatar';
import { ETemplateOwnerType } from '../../../types/template';

export interface IAvatarWithGroupProps extends IAvatarProps {
  user: TAvatarUser | IGroupAvatar;
}

export interface IGroupAvatar {
  type: ETemplateOwnerType.UserGroup;
  name: string;
}

export function AvatarWithGroup({ user, ...rest }: IAvatarWithGroupProps) {
  let currentData = user;

  if ('name' in user && user.type === ETemplateOwnerType.UserGroup) {
    currentData = {
      ...user,
      firstName: user.name,
    };
  }

  return <Avatar user={currentData} {...rest} />;
}
