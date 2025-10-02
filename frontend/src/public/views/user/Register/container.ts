import { connect } from 'react-redux';

import { registerUser } from '../../../redux/auth/actions';
import { IRegisterProps, Register } from './Register';

type TRegisterDispatchProps = Pick<IRegisterProps, 'registerUser'>;

const mapDispatchToProps: TRegisterDispatchProps = {
  registerUser,
};

export const RegisterContainer = connect<void, TRegisterDispatchProps>(null, mapDispatchToProps)(Register);
