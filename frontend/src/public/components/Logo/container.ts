/* prettier-ignore */
import { connect } from 'react-redux';
import type { IApplicationState } from '../../redux/store';

import { Logo, ILogoProps } from './Logo';

type TStoreProps = Pick<ILogoProps, 'partnerLogoLg' | 'partnerLogoSm'>;

const mapStateToProps = ({ authUser: { account } }: IApplicationState): TStoreProps => {
  return {
    partnerLogoSm: account.logoSm,
    partnerLogoLg: account.logoLg,
  };
};

export const LogoContainer = connect(mapStateToProps)(Logo);
