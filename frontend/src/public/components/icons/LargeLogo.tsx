import * as React from 'react';

import { BrandLockup } from '../Logo/BrandLockup';

export function LargeLogo(props: React.SVGAttributes<SVGSVGElement>) {
  return <BrandLockup variant="standard" {...props} />;
}
