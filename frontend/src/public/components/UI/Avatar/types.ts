import type { IUnsavedUser, TUserType } from '../../../types/user';

export type TAvatarUser = Partial<Pick<IUnsavedUser, 'firstName' | 'lastName' | 'email' | 'status' | 'photo'>> & {
  type?: TUserType;
};

export type TAvatarSize = 'xxl' | 'xl' | 'lg' | 'md' | 'sm';

export interface IAvatarProps {
  isSystemAvatar?: boolean;
  user?: TAvatarUser;
  size?: TAvatarSize;
  isEmpty?: boolean;
  sizeMobile?: TAvatarSize;
  containerClassName?: string;
  className?: string;
  showInitials?: boolean;
  withTooltip?: boolean;
}

export type TCurrentUserAvatarProps = Omit<IAvatarProps, 'user'>;
