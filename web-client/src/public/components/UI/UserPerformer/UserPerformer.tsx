import React from 'react';
import classnames from 'classnames';

import { Avatar } from "..";
import { DeleteRoundIcon } from '../../icons';
import { TUserListItem } from '../../../types/user';
import { getUserById } from '../../UserData/utils/getUserById';
import { ETaskPerformerType } from '../../../types/template';

import styles from './UserPerformer.css';

export interface IUserPerformerProps {
  users: TUserListItem[];
  user: any;
  bgColor?: EBgColorTypes;
  onClick?(): void;
}

export enum EBgColorTypes {
  White = 'white',
  Light = 'light',
  Orange = 'orange',
}

export const UserPerformerComponent = ({
  users,
  user,
  onClick,
  bgColor = EBgColorTypes.White,
}: IUserPerformerProps) => {
  const bgColorClassNameMap = {
    white: styles['is-white'],
    light: styles['is-light'],
    orange: styles['is-orange'],
  };

  const isTypeUser = user.type === ETaskPerformerType.User;
  const currentUser: any = isTypeUser && user.sourceId ? getUserById(users, +user.sourceId) : user;

  return (
    <div className={classnames(styles['user-performer'], bgColorClassNameMap[bgColor])}>
      {currentUser && (
        <Avatar
          isEmpty={!isTypeUser}
          size="sm"
          user={currentUser}
          containerClassName={styles['user-performer__avatar']}
          showInitials={false}
        />
      )}
      <p className={styles['user-performer__name']}>{user.label}</p>
      {onClick && (
        <button
          onClick={onClick}
          className={styles['user-performer__close']}
          type="button"
          aria-label="Delete performer"
        >
          <DeleteRoundIcon />
        </button>
      )}
    </div>
  );
};
