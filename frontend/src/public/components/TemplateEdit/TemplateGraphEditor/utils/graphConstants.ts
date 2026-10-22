/** Marker for the kick-off form as an edge source; the label is localized in the UI. */
export const KICKOFF_NODE_ID = 'kickoff';
export const KICKOFF_START_AFTER = '__kickoff__';
export const CHECK_IF_FORK_PREFIX = 'junction-fork-checkif-';
export const CHECK_IF_JOIN_PREFIX = 'junction-join-checkif-';

export function isCheckIfJunctionId(id: string): boolean {
  return id.startsWith(CHECK_IF_FORK_PREFIX) || id.startsWith(CHECK_IF_JOIN_PREFIX);
}

/** Card → its check-if fork, or check-if join → its card. Not a branch. */
export function isCheckIfStemEdge(sourceId: string, targetId: string): boolean {
  const intoFork = !isCheckIfJunctionId(sourceId) && targetId.startsWith(CHECK_IF_FORK_PREFIX);
  const outOfJoin = sourceId.startsWith(CHECK_IF_JOIN_PREFIX) && !isCheckIfJunctionId(targetId);

  return intoFork || outOfJoin;
}
