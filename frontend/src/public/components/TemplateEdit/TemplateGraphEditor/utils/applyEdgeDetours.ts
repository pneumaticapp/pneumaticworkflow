import { TGraphEdge, TGraphNode } from '../types';
import {
  GRAPH_EDGE_SIDEWAYS_THRESHOLD,
  GRAPH_SKIP_LANE_GAP,
  TGraphLaneSide,
  getGraphNodeBox,
  isCardNode,
} from './graphGeometry';

const CARD_HIT_INSET = 2;

function wouldAlignedEdgeCrossCard(
  source: TGraphNode,
  target: TGraphNode,
  nodes: TGraphNode[],
): boolean {
  const sourceBox = getGraphNodeBox(source);
  const targetBox = getGraphNodeBox(target);
  const top = sourceBox.bottom;
  const bottom = targetBox.y;

  if (bottom <= top) {
    return false;
  }

  const lineX = sourceBox.centerX;

  return nodes.some((node) => {
    if (node.id === source.id || node.id === target.id || !isCardNode(node)) {
      return false;
    }

    const box = getGraphNodeBox(node);
    const overlapsSource = box.bottom > sourceBox.y + CARD_HIT_INSET && box.y < sourceBox.bottom - CARD_HIT_INSET;
    const overlapsTarget = box.bottom > targetBox.y + CARD_HIT_INSET && box.y < targetBox.bottom - CARD_HIT_INSET;

    if (overlapsSource || overlapsTarget) {
      return false;
    }

    return (
      box.y < bottom - CARD_HIT_INSET
      && box.bottom > top + CARD_HIT_INSET
      && lineX > box.x + CARD_HIT_INSET
      && lineX < box.right - CARD_HIT_INSET
    );
  });
}

export function pickDetourSide(source: TGraphNode, target: TGraphNode, nodes: TGraphNode[]): TGraphLaneSide {
  const sourceBox = getGraphNodeBox(source);
  const targetBox = getGraphNodeBox(target);
  const top = Math.min(sourceBox.y, targetBox.y);
  const bottom = Math.max(sourceBox.bottom, targetBox.bottom);
  const lineX = sourceBox.centerX;

  let leftEdge = Math.min(sourceBox.x, targetBox.x);
  let rightEdge = Math.max(sourceBox.right, targetBox.right);

  nodes.forEach((node) => {
    if (!isCardNode(node) || node.id === source.id || node.id === target.id) {
      return;
    }

    const box = getGraphNodeBox(node);
    const overlaps = box.bottom > top && box.y < bottom;

    if (!overlaps) {
      return;
    }

    leftEdge = Math.min(leftEdge, box.x);
    rightEdge = Math.max(rightEdge, box.right);
  });

  const leftCost = lineX - leftEdge + GRAPH_SKIP_LANE_GAP;
  const rightCost = rightEdge - lineX + GRAPH_SKIP_LANE_GAP;

  return leftCost < rightCost ? 'left' : 'right';
}

/** A vertical stem that would cut through a card leaves the column and runs beside it. */
export function markDetourEdges(nodes: TGraphNode[], edges: TGraphEdge[]): TGraphEdge[] {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));

  return edges.map((edge) => {
    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);
    const restData = {
      ...edge.data,
      isLaneRouted: undefined,
      laneX: undefined,
      laneSide: undefined,
    };

    if (!source || !target) {
      return { ...edge, data: restData };
    }

    const deltaX = getGraphNodeBox(target).centerX - getGraphNodeBox(source).centerX;
    const needsDetour = Math.abs(deltaX) <= GRAPH_EDGE_SIDEWAYS_THRESHOLD
      && wouldAlignedEdgeCrossCard(source, target, nodes);

    if (!needsDetour) {
      return { ...edge, data: restData };
    }

    return {
      ...edge,
      data: {
        ...restData,
        isLaneRouted: true,
        laneSide: pickDetourSide(source, target, nodes),
      },
    };
  });
}
