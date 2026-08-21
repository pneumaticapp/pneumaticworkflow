import { TGraphEdge } from '../types';

export const GRAPH_EDGE_CLASS_SKIP = 'graph-edge--skip';

export const EDGE_STYLE_DEFAULT = {
  stroke: 'var(--pneumatic-color-black32)',
  strokeWidth: 1,
};

export const EDGE_STYLE_SKIP = {
  stroke: 'var(--pneumatic-color-link)',
  strokeWidth: 1,
  strokeDasharray: '6 4',
};

export const EDGE_STYLE_SKIP_FOCUSED = {
  stroke: 'var(--pneumatic-color-link-hover)',
  strokeWidth: 2,
};

export const EDGE_STYLE_FOCUSED = {
  stroke: 'var(--pneumatic-color-black100)',
  strokeWidth: 2,
};

export function isSkipGraphEdge(edge: TGraphEdge): boolean {
  return (
    edge.sourceHandle === 'source-skip' ||
    /-skip-\d+$/.test(edge.id) ||
    Boolean(edge.className?.split(' ').includes(GRAPH_EDGE_CLASS_SKIP))
  );
}
