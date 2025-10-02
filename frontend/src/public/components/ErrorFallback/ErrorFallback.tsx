import * as React from 'react';
import * as Sentry from '@sentry/react';

import { getWithExpiry } from './utils/getWithExpiry';
import { setWithExpiry } from './utils/setWithExpiry';
import { GeneralLoader } from '../GeneralLoader';

export interface IErrorFallbackProps {
  // tslint:disable-next-line: no-any
  error: any;
}

const LS_CHUNK_FAILED_FLAG = 'chunk_failed';
const chunkFailedMessage = /chunk/;

export function ErrorFallback({ error }: IErrorFallbackProps) {
  const isChunkError = error?.message && chunkFailedMessage.test(error.message);

  // Handle failed lazy loading of a JS/CSS chunk.
  React.useEffect(() => {
    Sentry.captureException(error);

    if (isChunkError) {
      if (!getWithExpiry(LS_CHUNK_FAILED_FLAG)) {
        setWithExpiry(LS_CHUNK_FAILED_FLAG, 'true', 10000);
        window.location.reload();
      }
    }
  }, [error]);

  if (isChunkError) {
    return <GeneralLoader />;
  }

  return (
    <div>
      <p>Something went wrong.</p>
      <pre>{error?.message}</pre>
    </div>
  );
}
