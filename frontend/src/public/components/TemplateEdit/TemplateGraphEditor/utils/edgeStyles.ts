import { CSSProperties } from 'react';
import { TGraphEdge, TGraphEdgeLine } from '../types';

export const GRAPH_EDGE_CLASS_CONDITIONAL = 'graph-edge--conditional';
export const GRAPH_EDGE_CLASS_SKIP = GRAPH_EDGE_CLASS_CONDITIONAL;

export const EDGE_STYLE_DEFAULT: CSSProperties = {
  stroke: 'var(--pneumatic-color-black32)',
  strokeWidth: 1,
};

export const EDGE_STYLE_CONDITIONAL: CSSProperties = {
  stroke: 'var(--pneumatic-color-link)',
  strokeWidth: 1,
  strokeDasharray: '6 4',
};

export const EDGE_STYLE_SKIP = EDGE_STYLE_CONDITIONAL;

export const EDGE_STYLE_CONDITIONAL_FOCUSED: CSSProperties = {
  stroke: 'var(--pneumatic-color-link-hover)',
  strokeWidth: 2,
};

export const EDGE_STYLE_SKIP_FOCUSED = EDGE_STYLE_CONDITIONAL_FOCUSED;

export const EDGE_STYLE_FOCUSED: CSSProperties = {
  stroke: 'var(--pneumatic-color-black100)',
  strokeWidth: 2,
};

export function isSkipGraphEdge(edge: TGraphEdge): boolean {
  return /-skip-\d+$/.test(edge.id);
}

export function isConditionalGraphEdge(edge: TGraphEdge): boolean {
  return (
    Boolean(edge.data?.isConditional) ||
    isSkipGraphEdge(edge) ||
    Boolean(edge.className?.split(' ').includes(GRAPH_EDGE_CLASS_CONDITIONAL)) ||
    Boolean(edge.className?.split(' ').includes('graph-edge--skip'))
  );
}

export function getGraphEdgeLine(edge: TGraphEdge): TGraphEdgeLine {
  return isConditionalGraphEdge(edge) ? 'dashed' : 'solid';
}

/** Lane lines bypass the junctions and run beside the column instead of the vertical stem. */
export function isLaneRoutedGraphEdge(edge: TGraphEdge): boolean {
  return isSkipGraphEdge(edge) || Boolean(edge.data?.isLaneRouted);
}

export function getGraphEdgeVisual(isConditional: boolean): {
  className?: string;
  style: CSSProperties;
} {
  if (isConditional) {
    return {
      className: GRAPH_EDGE_CLASS_CONDITIONAL,
      style: EDGE_STYLE_CONDITIONAL,
    };
  }

  return {
    style: EDGE_STYLE_DEFAULT,
  };
}
