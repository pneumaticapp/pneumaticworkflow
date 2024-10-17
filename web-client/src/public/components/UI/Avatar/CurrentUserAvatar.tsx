import * as React from 'react';
import { useSelector } from 'react-redux';

import { IAvatarProps, Avatar } from '.';

import { getAuthUser } from '../../../redux/selectors/user';

export type TCurrentUserAvatarProps = Omit<IAvatarProps, 'user'>;

export function CurrentUserAvatar(props: TCurrentUserAvatarProps) {
  const { authUser } = useSelector(getAuthUser)

  return <Avatar {...props} user={authUser} />;
}
