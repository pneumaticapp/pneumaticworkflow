export function isRequestCanceled(error: unknown): boolean {
  if (!error || typeof error !== 'object') {
    return false;
  }
  const err = error as { code?: string; name?: string };
  return err.code === 'ERR_CANCELED' || err.name === 'CanceledError';
}
