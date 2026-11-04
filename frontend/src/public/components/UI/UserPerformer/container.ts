import { connect } from 'react-redux';

import { UserPerformerComponent, IUserPerformerProps } from './UserPerformer';
import type { IApplicationState } from '../../../redux/store';

type TStoreProps = Pick<IUserPerformerProps, 'users'>;

const mapStateToProps = ({ accounts: { users } }: IApplicationState): TStoreProps => {
  return { users };
};

export const UserPerformer = connect(mapStateToProps)(UserPerformerComponent);
