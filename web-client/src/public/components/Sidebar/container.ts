import { withRouter } from 'react-router-dom';
import { compose } from 'redux';
import { injectIntl } from 'react-intl';
import { connect } from 'react-redux';

import { setContainerClassnames, openSelectTemplateModal, showPlanExpiredMessage } from '../../redux/actions';
import { IApplicationState } from '../../types/redux';
import { ISidebarDispatchProps, ISidebarProps, Sidebar } from './Sidebar';
import { getUserPendingActions } from '../../redux/selectors/user';

type TStoreProps = Pick<
  ISidebarProps,
  'containerClassnames' | 'menuHiddenBreakpoint' | 'menuItems' | 'authUser' | 'pendingActions'
>;

const mapStateToProps = (state: IApplicationState): TStoreProps => {
  const { menu, authUser } = state;
  const { containerClassnames, menuHiddenBreakpoint } = menu;
  const pendingActions = getUserPendingActions(state);

  return {
    containerClassnames,
    menuItems: menu.items,
    authUser,
    pendingActions,
    menuHiddenBreakpoint,
  };
};

export const mapDispatchToProps: ISidebarDispatchProps = {
  setContainerClassnames,
  openSelectTemplateModal,
  showPlanExpiredMessage,
};

export const SidebarContainer = compose(withRouter, injectIntl, connect(mapStateToProps, mapDispatchToProps))(Sidebar);
