import { connect } from 'react-redux';

import type { RootState } from '../../../redux/store';
import { registerUserInvited } from '../../../redux/auth/actions';
import type { IRegisterInviteProps } from './RegisterInvite';
import { RegisterInvite } from './RegisterInvite';

type TRegisterInviteProps = Pick<IRegisterInviteProps, 'id' | 'loading'>;
type TRegisterInviteDispatchProps = Pick<IRegisterInviteProps, 'registerUserInvited'>;

export const mapStateToProps = ({ authUser }: RootState): TRegisterInviteProps => {
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
