import React from 'react';
import { useSelector } from 'react-redux';

import { Avatar } from './Avatar';
import type { TCurrentUserAvatarProps } from './types';

import { getAuthUser } from '../../../redux/selectors/user';

export function CurrentUserAvatar(props: TCurrentUserAvatarProps) {
  const { authUser } = useSelector(getAuthUser);

  return <Avatar {...props} user={authUser} />;
}
