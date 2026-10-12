import * as Sentry from '@sentry/react';
import { logger } from '../utils/logger';

const NETWORK_ERROR_FLUSH_DELAY_MS = 5000;
const NETWORK_ERROR_MAX_WAIT_MS = 30000;
let networkErrorBuffer: { method?: string; url?: string }[] = [];
let networkErrorFlushTimer: ReturnType<typeof setTimeout> | null = null;
let firstErrorTimestamp: number | null = null;

export function flushNetworkErrors() {
  if (networkErrorBuffer.length === 0) return;
  const requests = networkErrorBuffer;
  networkErrorBuffer = [];
  networkErrorFlushTimer = null;
  firstErrorTimestamp = null;

  const count = requests.length;
  const message = `Network Error Burst: ${count} ${count === 1 ? 'request' : 'requests'} failed`;

  Sentry.withScope((scope) => {
    scope.setExtra('count', count);
    scope.setExtra('requests', requests);
    logger.error(message);
  });
}

export function bufferNetworkError(request: { method?: string; url?: string }) {
  const now = Date.now();

  networkErrorBuffer.push(request);

  if (firstErrorTimestamp === null) {
    firstErrorTimestamp = now;
  }

  if (now - firstErrorTimestamp >= NETWORK_ERROR_MAX_WAIT_MS) {
    if (networkErrorFlushTimer) clearTimeout(networkErrorFlushTimer);
    flushNetworkErrors();
    return;
  }

  if (networkErrorFlushTimer) clearTimeout(networkErrorFlushTimer);
  networkErrorFlushTimer = setTimeout(flushNetworkErrors, NETWORK_ERROR_FLUSH_DELAY_MS);
}

export function resetNetworkErrorBuffer() {
  networkErrorBuffer = [];
  firstErrorTimestamp = null;
  if (networkErrorFlushTimer) {
    clearTimeout(networkErrorFlushTimer);
    networkErrorFlushTimer = null;
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', flushNetworkErrors);
}
