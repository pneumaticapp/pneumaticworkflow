import { connect } from 'react-redux';

import { registerUser } from '../../../redux/auth/actions';
import type { IRegisterProps } from './Register';
import { Register } from './Register';

type TRegisterDispatchProps = Pick<IRegisterProps, 'registerUser'>;

const mapDispatchToProps: TRegisterDispatchProps = {
  registerUser,
};

export const RegisterContainer = connect<void, TRegisterDispatchProps>(null, mapDispatchToProps)(Register);
