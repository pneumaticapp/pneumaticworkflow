/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { useCheckDevice } from '../../hooks/useCheckDevice';

interface IMediaProps {
  children: React.ReactNode;
}

export function Desktop({ children }: IMediaProps) {
  const { isDesktop } = useCheckDevice();

  if (!isDesktop) {
    return null;
  }

  return <>{children}</>;
}

export function Mobile({ children }: IMediaProps) {
  const { isMobile } = useCheckDevice();

  if (!isMobile) {
    return null;
  }

  return <>{children}</>;
}
