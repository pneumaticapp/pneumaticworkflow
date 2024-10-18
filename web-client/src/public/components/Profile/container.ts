import { connect } from 'react-redux';
import { IProfileProps, Profile } from './Profile';
import { IApplicationState } from '../../types/redux';
import { editCurrentUser, sendChangePassword } from '../../redux/auth/actions';
import { setProfileSettingsActiveTab } from '../../redux/profile/actions';

type TProfileProps = Pick<IProfileProps, 'user'>;
type TProfileDispatchProps = Pick<IProfileProps, 'editCurrentUser' | 'sendChangePassword' | 'onChangeTab'>;

export function mapStateToProps({ authUser }: IApplicationState): TProfileProps {
  return {
    user: authUser,
  };
}

export const mapDispatchToProps: TProfileDispatchProps = {
  editCurrentUser,
  sendChangePassword,
  onChangeTab: setProfileSettingsActiveTab,
};

export const ProfileContainer = connect<TProfileProps, TProfileDispatchProps>
(mapStateToProps, mapDispatchToProps)(Profile);
