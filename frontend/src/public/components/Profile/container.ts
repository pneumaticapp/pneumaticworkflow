import { connect } from 'react-redux';
import { IProfileProps, Profile } from './Profile';
import { IApplicationState } from '../../types/redux';
import { editCurrentUser, sendChangePassword, vacationActivate, vacationDeactivate } from '../../redux/auth/actions';
import { setProfileSettingsActiveTab } from '../../redux/profile/actions';

type TProfileProps = Pick<IProfileProps, 'user' | 'availableUsers'>;
type TProfileDispatchProps = Pick<
  IProfileProps,
  'editCurrentUser' | 'sendChangePassword' | 'onChangeTab' | 'onVacationActivate' | 'onVacationDeactivate'
>;

export function mapStateToProps({ authUser, accounts }: IApplicationState): TProfileProps {
  return {
    user: authUser,
    availableUsers: (accounts.users || [])
      .filter((u) => u.id !== authUser.id && u.status === 'active'),
  };
}

export const mapDispatchToProps: TProfileDispatchProps = {
  editCurrentUser,
  sendChangePassword,
  onChangeTab: setProfileSettingsActiveTab,
  onVacationActivate: vacationActivate,
  onVacationDeactivate: vacationDeactivate,
};

export const ProfileContainer = connect<TProfileProps, TProfileDispatchProps>
(mapStateToProps, mapDispatchToProps)(Profile);
