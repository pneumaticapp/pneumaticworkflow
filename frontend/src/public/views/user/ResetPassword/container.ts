import { connect } from 'react-redux';

import type { IResetPasswordProps } from './ResetPassword';
import { ResetPassword } from './ResetPassword';
import type { RootState } from '../../../redux/store';
import { sendResetPassword } from '../../../redux/auth/actions';

type TResetPasswordProps = Pick<IResetPasswordProps, 'loading'>;
type TResetPasswordDispatchProps = Pick<IResetPasswordProps, 'sendResetPassword'>;

export const mapStateToProps = ({ authUser }: RootState): TResetPasswordProps => {
  return { loading: authUser.loading };
};

export const mapDispatchToProps: TResetPasswordDispatchProps = {
  sendResetPassword,
};

export const ResetPasswordContainer = connect<TResetPasswordProps, TResetPasswordDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(ResetPassword);
