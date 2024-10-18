import { connect } from 'react-redux';

import { UserDataComponent, IUserdataProps } from './UserData';
import { IApplicationState } from '../../types/redux';
import { getUserById } from './utils/getUserById';

type TStoreProps = Pick<IUserdataProps, 'user'>;
type TOwnProps = Pick<IUserdataProps, 'userId'>;

const mapStateToProps = (
  { accounts: { users } }: IApplicationState,
  { userId }: TOwnProps,
): TStoreProps => {
  return { user: getUserById(users, userId) };
};

export const UserData = connect(mapStateToProps)(UserDataComponent);
