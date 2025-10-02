import { connect } from 'react-redux';

import { ILoginProps, Login } from './Login';
import { IApplicationState } from '../../../types/redux';
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
