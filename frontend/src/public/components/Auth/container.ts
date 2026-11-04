import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';

import { Auth, IAuthUserProps } from './Auth';
import type { RootState } from '../../redux/store';
import { logoutUser } from '../../redux/auth/actions';

type TAuthUserStoreProps = Pick<IAuthUserProps, 'email'>;
type TAuthUserDispatchProps = Pick<IAuthUserProps, 'logout'>;

const mapStateToProps = ({ authUser }: RootState): TAuthUserStoreProps => {
  const { email } = authUser;

  return { email };
};

const mapDispatchToProps: TAuthUserDispatchProps = { logout: logoutUser };

export const AuthContainer = withRouter(
  connect<TAuthUserStoreProps, TAuthUserDispatchProps>(mapStateToProps, mapDispatchToProps)(Auth),
);
