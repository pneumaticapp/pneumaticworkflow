import { connect } from 'react-redux';

import { ForgotPassword, IForgotPasswordProps } from './ForgotPassword';
import { IApplicationState } from '../../../types/redux';
import { sendForgotPassword } from '../../../redux/auth/actions';

type TLoginProps = Pick<IForgotPasswordProps, 'loading'>;
type TLoginDispatchProps = Pick<IForgotPasswordProps, 'sendForgotPassword'>;

export const mapStateToProps = ({ authUser }: IApplicationState): TLoginProps => {
  return { loading: authUser.loading };
};

export const mapDispatchToProps: TLoginDispatchProps = {
  sendForgotPassword,
};

export const ForgotPasswordContainer = connect<TLoginProps, TLoginDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(ForgotPassword);
