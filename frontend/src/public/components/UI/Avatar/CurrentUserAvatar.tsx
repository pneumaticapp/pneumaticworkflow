import * as React from 'react';
import { useSelector } from 'react-redux';

import { Avatar } from './Avatar';
import type { IAvatarProps } from './Avatar';

import { getAuthUser } from '../../../redux/selectors/user';

export type TCurrentUserAvatarProps = Omit<IAvatarProps, 'user'>;

export function CurrentUserAvatar(props: TCurrentUserAvatarProps) {
  const { authUser } = useSelector(getAuthUser);

  return <Avatar {...props} user={authUser} />;
}
