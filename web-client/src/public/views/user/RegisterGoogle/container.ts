import { connect } from 'react-redux';

import { IApplicationState } from '../../../types/redux';
import { registerUser, removeGoogleUser } from '../../../redux/auth/actions';
import { IRegisterGoogleProps, RegisterGoogle } from './RegisterGoogle';

type TRegisterStoreProps = Pick<IRegisterGoogleProps, 'googleAuthUserInfo'>;
type TRegisterDispatchProps = Pick<IRegisterGoogleProps, 'registerUser' | 'removeGoogleUser'>;

export const mapStateToProps = ({ authUser }: IApplicationState): TRegisterStoreProps => {
  const { googleAuthUserInfo } = authUser;

  return { googleAuthUserInfo };
};

const mapDispatchToProps: TRegisterDispatchProps = {
  registerUser,
  removeGoogleUser
};

export const RegisterGoogleContainer = connect<TRegisterStoreProps, TRegisterDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(RegisterGoogle);
