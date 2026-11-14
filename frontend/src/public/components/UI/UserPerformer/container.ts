import { connect } from 'react-redux';

import type { IUserPerformerProps } from './UserPerformer';
import { UserPerformerComponent } from './UserPerformer';
import type { RootState } from '../../../redux/store';

type TStoreProps = Pick<IUserPerformerProps, 'users'>;

const mapStateToProps = ({ accounts: { users } }: RootState): TStoreProps => {
  return { users };
};

export const UserPerformer = connect(mapStateToProps)(UserPerformerComponent);
