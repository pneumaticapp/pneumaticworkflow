import { connect } from 'react-redux';

import type { ISuperuserLoginProps } from './SuperuserLogin';
import { SuperuserLogin } from './SuperuserLogin';
import type { RootState } from '../../../redux/store';
import { loginSuperuser } from '../../../redux/auth/actions';

type TSuperuserLoginProps = Pick<ISuperuserLoginProps, 'loading' | 'isSuperuser'>;
type TSuperuserLoginDispatchProps = Pick<ISuperuserLoginProps, 'loginSuperuser'>;

export const mapStateToProps = ({ authUser }: RootState): TSuperuserLoginProps => {
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
