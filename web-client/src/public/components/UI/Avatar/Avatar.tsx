import * as React from 'react';
import * as classnames from 'classnames';

import { EUserStatus, IUnsavedUser, TUserType } from '../../../types/user';
import { getUserFullName } from '../../../utils/users';
import { CustomTooltip } from '../CustomTooltip';
import { ExternalUserAvatarIcon, GuestUserAvatarIcon, PneumaticAvatarIcon } from '../../icons';

import styles from './Avatar.css';

export type TAvatarUser = Pick<IUnsavedUser, 'firstName' | 'lastName' | 'email' | 'status' | 'photo'> & {
  type?: TUserType;
};
type TAvatarSize = 'xxl' | 'xl' | 'lg' | 'md' | 'sm';

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

export const getBackgroundColor = (fullName: string) => {
  const name = [...fullName];
  const hash = name.reduce((result, char) => {
    // eslint-disable-next-line no-bitwise
    return char.charCodeAt(0) + ((result << 2) - result);
  }, 0) % 360;

  return `hsl(${hash}, 60%, 60%)`;
};

const getInitials = (firstName: string, lastName: string) => {
  if (!firstName && !lastName) {
    return null;
  }

  return [firstName, lastName]
    .map(name => name.slice(0, 1).toUpperCase())
    .join('');
};

export function Avatar({
  className,
  containerClassName,
  user,
  isSystemAvatar,
  showInitials = true,
  size = 'md',
  sizeMobile,
  withTooltip,
  isEmpty,
}: IAvatarProps) {
  const tooltipTargerRef = React.useRef<HTMLDivElement>(null);
  const avatarSizeClassMap: { [key in TAvatarSize]: string } = {
    xxl: styles['avatar_xxl'],
    xl: styles['avatar_xl'],
    lg: styles['avatar_lg'],
    md: styles['avatar_md'],
    sm: styles['avatar_sm'],
  };
  const avatarSizeMobileClassMap: { [key in TAvatarSize]: string } = {
    xxl: styles['avatar_mobile-xxl'],
    xl: styles['avatar_mobile-xl'],
    lg: styles['avatar_mobile-lg'],
    md: styles['avatar_mobile-md'],
    sm: styles['avatar_mobile-sm'],
  };
  const sizeClasses = [
    avatarSizeClassMap[size],
    sizeMobile && avatarSizeMobileClassMap[sizeMobile],
  ];

  if (isSystemAvatar) {
    return <PneumaticAvatarIcon className={classnames(...sizeClasses, className)} />;
  }

  if (isEmpty) {
    return (
      <div className={containerClassName} >
        <div className={classnames(styles['avatar'], ...sizeClasses, styles['avatar_empty'], className)} />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const {
    firstName,
    lastName,
    photo,
  } = user;
  const initials = getInitials(firstName, lastName);
  const fullName = getUserFullName(user);

  const renderImage = () => {
    if (user.type === 'guest') {
      return <GuestUserAvatarIcon className={classnames(styles['avatar'], ...sizeClasses, className)} />;
    }

    const notRegistratedStatues = [EUserStatus.Invited, EUserStatus.External];
    if (user.status && notRegistratedStatues.includes(user.status)) {
      return <ExternalUserAvatarIcon className={classnames(styles['avatar'], ...sizeClasses, className)} />;
    }

    if (photo) {
      return <img className={classnames(styles['avatar'], ...sizeClasses, className)} alt="Profile" src={photo} />;
    }

    if (user.status === EUserStatus.Deleted) {
      return <div className={classnames(styles['avatar'], ...sizeClasses, styles['avatar_empty'], className)} />;
    }

    const backgroundColor = getBackgroundColor(fullName);

    return (
      <div
        style={{ backgroundColor: `${backgroundColor}` }}
        className={classnames(styles['avatar'], ...sizeClasses, className)}
      >
        {showInitials && <span className={styles['initials']}>{initials}</span>}
      </div>
    );
  };

  return (
    <div className={containerClassName} ref={tooltipTargerRef} >
      {renderImage()}
      {withTooltip && (
        <CustomTooltip
          target={tooltipTargerRef}
          tooltipText={fullName}
        />
      )}
    </div>
  );
}
