import { connect } from 'react-redux';

import { SuperuserLogin, ISuperuserLoginProps } from './SuperuserLogin';
import type { IApplicationState } from '../../../redux/store';
import { loginSuperuser } from '../../../redux/auth/actions';

type TSuperuserLoginProps = Pick<ISuperuserLoginProps, 'loading' | 'isSuperuser'>;
type TSuperuserLoginDispatchProps = Pick<ISuperuserLoginProps, 'loginSuperuser'>;

export const mapStateToProps = ({ authUser }: IApplicationState): TSuperuserLoginProps => {
  return {
    isSuperuser: authUser.isSuperuser,
    loading: authUser.loading,
  };
};

export const mapDispatchToProps: TSuperuserLoginDispatchProps = {
  loginSuperuser,
};

export const SuperuserLoginContainer = connect<TSuperuserLoginProps, TSuperuserLoginDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SuperuserLogin);
