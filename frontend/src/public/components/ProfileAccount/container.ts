import { connect } from 'react-redux';
import { IProfileAccountProps, ProfileAccount } from './ProfileAccount';
import { IApplicationState } from '../../types/redux';
import { editCurrentAccount } from '../../redux/auth/actions';
import { setProfileSettingsActiveTab } from '../../redux/profile/actions';

type TProfileAccountProps = Pick<
  IProfileAccountProps,
  'loading' | 'accountId' | 'name' | 'isAdmin' | 'logoSm' | 'logoLg' | 'billingPlan' | 'leaseLevel'
>;
type TProfileAccountDispatchProps = Pick<IProfileAccountProps, 'editCurrentAccount' | 'onChangeTab'>;

export function mapStateToProps({ authUser, accounts: { planInfo } }: IApplicationState): TProfileAccountProps {
  const { account, loading, isAdmin } = authUser;

  return {
    loading,
    accountId: account.id,
    name: account.name,
    isAdmin,
    logoSm: account.logoSm,
    logoLg: account.logoLg,
    leaseLevel: account.leaseLevel,
    billingPlan: planInfo.billingPlan,
  };
}

export const mapDispatchToProps: TProfileAccountDispatchProps = {
  editCurrentAccount,
  onChangeTab: setProfileSettingsActiveTab,
};

export const ProfileAccountContainer = connect<TProfileAccountProps, TProfileAccountDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(ProfileAccount);
