import { connect } from 'react-redux';

import type { IUserLayoutProps } from './UserLayout';
import { UserLayout } from './UserLayout';
import type { RootState } from '../../redux/store';

type TUserLayoutStoreProps = Pick<IUserLayoutProps, 'pages'>;

export const mapStateToProps = ({ pages: { list } }: RootState): TUserLayoutStoreProps => {
  return { pages: list };
};

export const UserLayoutContainer = connect(mapStateToProps)(UserLayout);
