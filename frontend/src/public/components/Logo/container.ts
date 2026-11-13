/* prettier-ignore */
import { connect } from 'react-redux';
import type { RootState } from '../../redux/store';

import type { ILogoProps } from './Logo';
import { Logo } from './Logo';

type TStoreProps = Pick<ILogoProps, 'partnerLogoLg' | 'partnerLogoSm'>;

const mapStateToProps = ({ authUser: { account } }: RootState): TStoreProps => {
  return {
    partnerLogoSm: account.logoSm,
    partnerLogoLg: account.logoLg,
  };
};

export const LogoContainer = connect(mapStateToProps)(Logo);
