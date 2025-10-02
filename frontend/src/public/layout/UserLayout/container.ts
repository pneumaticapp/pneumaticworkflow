import { connect } from 'react-redux';

import { IUserLayoutProps, UserLayout } from './UserLayout';
import { IApplicationState } from '../../types/redux';

type TUserLayoutStoreProps = Pick<IUserLayoutProps, 'pages'>;

export const mapStateToProps = ({ pages: { list } }: IApplicationState): TUserLayoutStoreProps => {
  return { pages: list };
};

export const UserLayoutContainer = connect(mapStateToProps)(UserLayout);
