import { connect } from 'react-redux';

import { IUserLayoutProps, UserLayout } from './UserLayout';
import type { RootState } from '../../redux/store';

type TUserLayoutStoreProps = Pick<IUserLayoutProps, 'pages'>;

export const mapStateToProps = ({ pages: { list } }: RootState): TUserLayoutStoreProps => {
  return { pages: list };
};

export const UserLayoutContainer = connect(mapStateToProps)(UserLayout);
