import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { compose } from 'redux';

import { App, IAppProps } from './App';
import { IApplicationState } from '../../types/redux';
import { logoutUser } from '../../redux/actions';

type TAppStoreProps = Pick<
  IAppProps,
  | 'locale'
  | 'user'
  | 'hasNewTasks'
  | 'hasNewNotifications'
  | 'containerClassnames'
  | 'isFullscreenImageOpen'
>;
type TAppDispatchProps = Pick<IAppProps, 'logoutUser'>;

const mapStateToProps = ({
  general: {
    fullscreenImage: { isOpen: isFullscreenImageOpen },
  },
  tasks: { hasNewTasks },
  notifications: { hasNewNotifications },
  settings: { locale },
  authUser,
  menu: { containerClassnames },
}: IApplicationState): TAppStoreProps => {

  return {
    locale,
    user: authUser,
    hasNewTasks,
    hasNewNotifications,
    containerClassnames,
    isFullscreenImageOpen,
  };
};

const mapDispatchToProps: TAppDispatchProps = {
  logoutUser,
};

export const AppContainer: any = compose(
  withRouter, // crucial for correct router work
  connect<TAppStoreProps, TAppDispatchProps>(mapStateToProps, mapDispatchToProps),
)(App);
