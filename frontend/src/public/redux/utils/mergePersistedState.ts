import merge from 'lodash.merge';

export function mergePersistedState<TState, TInbound extends object | undefined = Partial<TState>>(
  inbound: TInbound,
  original: TState,
): TState {
  return merge({}, original, inbound);
}
