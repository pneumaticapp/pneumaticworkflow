export type TAutosavePersistScope = { generation: number };

export type TAutosavePersistRequest = {
  scope: TAutosavePersistScope;
  generation: number;
};

export function createAutosavePersistScope(): TAutosavePersistScope {
  return { generation: 0 };
}

export function allocateAutosavePersistRequest(
  scope: TAutosavePersistScope,
): TAutosavePersistRequest {
  scope.generation += 1;
  return { scope, generation: scope.generation };
}

export function abandonAutosavePersistRequests(scope: TAutosavePersistScope): void {
  scope.generation += 1;
}

export function isAutosavePersistRequestCurrent(
  request: TAutosavePersistRequest | undefined,
): boolean {
  return request === undefined || request.generation === request.scope.generation;
}
