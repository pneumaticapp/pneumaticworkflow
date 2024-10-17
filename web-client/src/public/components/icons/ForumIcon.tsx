/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { EIconSize } from '../../types/common';

export interface IForumIconProps extends React.SVGAttributes<SVGElement> {
  visible?: boolean;
  iconSize?: EIconSize;
}

export function ForumIcon({ fill= '#fee55a', visible = true, iconSize = EIconSize.Mobile, ...rest }: IForumIconProps) {
  if (!visible) {
    return null;
  }

  if (iconSize === EIconSize.Mobile) {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14" fill={fill} {...rest}>
        <path fillRule="evenodd" clipRule="evenodd" d="M9.66634 0.333496H0.999674C0.633008 0.333496 0.333008 0.633496 0.333008 1.00016V10.3335L2.99967 7.66683H9.66634C10.033 7.66683 10.333 7.36683 10.333 7.00016V1.00016C10.333 0.633496 10.033 0.333496 9.66634 0.333496ZM8.99967 1.66683V6.3335H2.44634L1.66634 7.1135V1.66683H8.99967ZM11.6663 3.00016H12.9997C13.3663 3.00016 13.6663 3.30016 13.6663 3.66683V13.6668L10.9997 11.0002H3.66634C3.29967 11.0002 2.99967 10.7002 2.99967 10.3335V9.00016H11.6663V3.00016Z" />
      </svg>
    );
  }

  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill={fill} xmlns="http://www.w3.org/2000/svg" {...rest}>
      <path fillRule="evenodd" clipRule="evenodd" d="M19.3327 0.666626H1.99935C1.26602 0.666626 0.666016 1.26663 0.666016 1.99996V20.6666L5.99935 15.3333H19.3327C20.066 15.3333 20.666 14.7333 20.666 14V1.99996C20.666 1.26663 20.066 0.666626 19.3327 0.666626ZM17.9993 3.33329V12.6666H4.89268L3.33268 14.2266V3.33329H17.9993ZM23.3327 5.99996H25.9993C26.7327 5.99996 27.3327 6.59996 27.3327 7.33329V27.3333L21.9993 22H7.33268C6.59935 22 5.99935 21.4 5.99935 20.6666V18H23.3327V5.99996Z" fill={fill} />
    </svg>
  );
}
