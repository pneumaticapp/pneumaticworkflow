import * as React from 'react';

import { BrandLockup } from '../Logo/BrandLockup';

export type TLogoWideProps = React.SVGAttributes<SVGSVGElement>;

export const LogoWide = (props: TLogoWideProps) => <BrandLockup variant="wide" tone="light" {...props} />;
