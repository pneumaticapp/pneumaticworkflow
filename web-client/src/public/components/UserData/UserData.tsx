import * as React from 'react';

import { TUserListItem } from '../../types/user';

export interface IUserdataProps {
  userId?: number | null;
  user: TUserListItem | null;
  children(user: TUserListItem | null): React.ReactNode;
}

export function UserDataComponent({ children, user }: IUserdataProps) {
  return <>{children(user)}</>;
}
