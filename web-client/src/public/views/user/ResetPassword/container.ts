import { connect } from 'react-redux';

import { ResetPassword, IResetPasswordProps } from './ResetPassword';
import { IApplicationState } from '../../../types/redux';
import { sendResetPassword } from '../../../redux/auth/actions';

type TResetPasswordProps = Pick<IResetPasswordProps, 'loading'>;
type TResetPasswordDispatchProps = Pick<IResetPasswordProps, 'sendResetPassword'>;

export const mapStateToProps = ({ authUser }: IApplicationState): TResetPasswordProps => {
  return { loading: authUser.loading };
};

export const mapDispatchToProps: TResetPasswordDispatchProps = {
  sendResetPassword,
};

export const ResetPasswordContainer = connect<TResetPasswordProps, TResetPasswordDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(ResetPassword);
