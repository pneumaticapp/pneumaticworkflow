/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { SettingsLayoutComponent, ISettingsLayoutComponentProps } from './SettingsLayout';
import { IApplicationState } from '../../types/redux';
import { setProfileSettingsActiveTab } from '../../redux/profile/actions';

export type TMapStateToProps = Pick<ISettingsLayoutComponentProps, 'activeTab'>;
export type TMapDispatchToProps = Pick<ISettingsLayoutComponentProps, 'onChangeTab'>;

export const mapStateToProps = ({ profile: { settingsTab } }: IApplicationState): TMapStateToProps => {
  return {
    activeTab: settingsTab,
  };
};

export const mapDispatchToProps: TMapDispatchToProps = {
  onChangeTab: setProfileSettingsActiveTab,
};

export const SettingsLayout = connect<TMapStateToProps, TMapDispatchToProps>
(mapStateToProps, mapDispatchToProps)(SettingsLayoutComponent);
