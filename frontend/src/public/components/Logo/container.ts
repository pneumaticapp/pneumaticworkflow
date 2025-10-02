/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';

import { Logo, ILogoProps } from './Logo';

type TStoreProps = Pick<ILogoProps, 'partnerLogoLg' | 'partnerLogoSm'>;

const mapStateToProps = (
  {
    authUser: { account },
  }: IApplicationState,
): TStoreProps => {

  return {
    partnerLogoSm: account.logoSm,
    partnerLogoLg: account.logoLg,
  };
};

export const LogoContainer = connect(mapStateToProps)(Logo);
