let autosavePersistRequestId = 0;

export function allocateAutosavePersistRequestId(): number {
  autosavePersistRequestId += 1;
  return autosavePersistRequestId;
}

export function abandonAutosavePersistRequests(): number {
  autosavePersistRequestId += 1;
  return autosavePersistRequestId;
}

export function isAutosavePersistRequestCurrent(requestId: number | undefined): boolean {
  return requestId === undefined || requestId === autosavePersistRequestId;
}

export function resetAutosavePersistRequestsForTests(): void {
  autosavePersistRequestId = 0;
}
