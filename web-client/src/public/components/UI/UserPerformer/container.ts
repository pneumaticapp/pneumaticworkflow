import { connect } from 'react-redux';

import { UserPerformerComponent, IUserPerformerProps } from './UserPerformer';
import { IApplicationState } from '../../../types/redux';

type TStoreProps = Pick<IUserPerformerProps, 'users'>;

const mapStateToProps = (
  { accounts: { users } }: IApplicationState,
): TStoreProps => {
  return { users };
};

export const UserPerformer = connect(mapStateToProps)(UserPerformerComponent);
