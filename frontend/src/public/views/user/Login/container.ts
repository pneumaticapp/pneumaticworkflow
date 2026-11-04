import { connect } from 'react-redux';

import { Login } from './Login';
import { ILoginProps } from './types';
import type { IApplicationState } from '../../../redux/store';
import { loginUser, setRedirectUrl } from '../../../redux/auth/actions';

type TLoginProps = Pick<ILoginProps, 'loading' | 'error'>;
type TLoginDispatchProps = Pick<ILoginProps, 'loginUser' | 'setRedirectUrl'>;

const mapStateToProps = ({ authUser }: IApplicationState): TLoginProps => {
  const { error, loading } = authUser;

  return { error, loading };
};

const mapDispatchToProps: TLoginDispatchProps = {
  loginUser,
  setRedirectUrl,
};

export const LoginContainer = connect<TLoginProps, TLoginDispatchProps>(mapStateToProps, mapDispatchToProps)(Login);
