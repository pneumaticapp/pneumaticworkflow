import * as React from 'react';

import { captureException } from '../../utils/sentryCapture';
import { getWithExpiry } from './utils/getWithExpiry';
import { setWithExpiry } from './utils/setWithExpiry';
import { GeneralLoader } from '../GeneralLoader';

export interface IErrorFallbackProps {
  error: Error | unknown;
}

const LS_CHUNK_FAILED_FLAG = 'chunk_failed';
const chunkFailedMessage = /chunk/;

function getErrorMessage(error: Error | unknown): string | undefined {
  if (error instanceof Error) return error.message;
  if (error !== null && typeof error === 'object' && 'message' in error && typeof (error as { message: unknown }).message === 'string') {
    return (error as { message: string }).message;
  }
  return undefined;
}

export function ErrorFallback({ error }: IErrorFallbackProps) {
  const message = getErrorMessage(error);
  const isChunkError = message !== undefined && chunkFailedMessage.test(message);

  React.useEffect(() => {
    const err = error instanceof Error ? error : new Error(getErrorMessage(error) ?? String(error));
    captureException(err);

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
      <pre>{message ?? String(error)}</pre>
    </div>
  );
}
