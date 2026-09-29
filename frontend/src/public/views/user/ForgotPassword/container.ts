import { connect } from 'react-redux';

import { ForgotPassword } from './ForgotPassword';
import { IForgotPasswordProps } from './types';
import { IApplicationState } from '../../../types/redux';
import { sendForgotPassword } from '../../../redux/auth/actions';

type TLoginProps = Pick<IForgotPasswordProps, 'loading' | 'isCaptchaRequired'>;
type TLoginDispatchProps = Pick<IForgotPasswordProps, 'sendForgotPassword'>;

export const mapStateToProps = ({ authUser }: IApplicationState): TLoginProps => {
  return { loading: authUser.loading, isCaptchaRequired: authUser.isResetPasswordCaptchaRequired };
};

export const mapDispatchToProps: TLoginDispatchProps = {
  sendForgotPassword,
};

export const ForgotPasswordContainer = connect<TLoginProps, TLoginDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(ForgotPassword);
