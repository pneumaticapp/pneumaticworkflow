import { connect } from 'react-redux';

import { IApplicationState } from '../../../types/redux';
import { registerUserInvited } from '../../../redux/auth/actions';
import { IRegisterInviteProps, RegisterInvite } from './RegisterInvite';

type TRegisterInviteProps = Pick<IRegisterInviteProps, 'id' | 'loading'>;
type TRegisterInviteDispatchProps = Pick<IRegisterInviteProps, 'registerUserInvited'>;

export const mapStateToProps = ({ authUser }: IApplicationState): TRegisterInviteProps => {
  const {
    loading,
    invitedUser: { id },
  } = authUser;

  return {
    id,
    loading,
  };
};

const mapDispatchToProps: TRegisterInviteDispatchProps = {
  registerUserInvited,
};

export const RegisterInviteContainer = connect<TRegisterInviteProps, TRegisterInviteDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(RegisterInvite);
