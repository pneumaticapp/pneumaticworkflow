import { connect } from 'react-redux';

import { IUserLayoutProps, UserLayout } from './UserLayout';
import type { IApplicationState } from '../../redux/store';

type TUserLayoutStoreProps = Pick<IUserLayoutProps, 'pages'>;

export const mapStateToProps = ({ pages: { list } }: IApplicationState): TUserLayoutStoreProps => {
  return { pages: list };
};

export const UserLayoutContainer = connect(mapStateToProps)(UserLayout);
