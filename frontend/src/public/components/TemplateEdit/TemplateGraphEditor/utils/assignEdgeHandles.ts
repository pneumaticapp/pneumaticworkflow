import { TGraphEdge, TGraphNode } from '../types';
import { isConditionalGraphEdge, isLaneRoutedGraphEdge } from './edgeStyles';
import { isCheckIfJunctionId } from './graphConstants';
import {
  GRAPH_EDGE_SIDEWAYS_THRESHOLD,
  IGraphNodeBox,
  TGraphFace,
  faceFromHandle,
  getGraphNodeBox,
  getJunctionKind,
  handleForFace,
  isCardNode,
  isJunctionNode,
  preferredFaces,
  sharesStemX,
} from './graphGeometry';

export interface IEdgeHandles {
  sourceHandle: string;
  targetHandle: string;
}

interface ISideItem {
  id: string;
  dx: number;
}

function assignOppositeSides(items: ISideItem[]): Map<string, TGraphFace> {
  const faces = new Map<string, TGraphFace>();

  if (items.length === 0) {
    return faces;
  }

  if (items.length === 1) {
    let face: TGraphFace = 'right';
    if (Math.abs(items[0].dx) <= GRAPH_EDGE_SIDEWAYS_THRESHOLD) {
      face = 'bottom';
    } else if (items[0].dx < 0) {
      face = 'left';
    }

    faces.set(items[0].id, face);

    return faces;
  }

  const left = items[0];
  const right = items[items.length - 1];
  const leftIsLeft = left.dx < -GRAPH_EDGE_SIDEWAYS_THRESHOLD;
  const rightIsRight = right.dx > GRAPH_EDGE_SIDEWAYS_THRESHOLD;

  if (items.length === 2 && leftIsLeft && rightIsRight) {
    faces.set(left.id, 'left');
    faces.set(right.id, 'right');

    return faces;
  }

  if (items.length === 2 && !rightIsRight && leftIsLeft) {
    faces.set(left.id, 'left');
    faces.set(right.id, 'bottom');

    return faces;
  }

  if (items.length === 2 && !leftIsLeft && rightIsRight) {
    faces.set(left.id, 'bottom');
    faces.set(right.id, 'right');

    return faces;
  }

  faces.set(left.id, 'left');
  faces.set(right.id, 'right');
  items.slice(1, -1).forEach((item) => {
    faces.set(item.id, 'bottom');
  });

  return faces;
}

function isStackedFace(face: TGraphFace): boolean {
  return face === 'top' || face === 'bottom';
}

const STEM_CARD_FACES: TGraphFace[] = ['bottom', 'top'];
const CHECK_IF_FACES: TGraphFace[] = ['left', 'right'];
const FACE_FALLBACK: TGraphFace[] = ['left', 'right', 'bottom', 'top'];

function allowedFaces(node: TGraphNode, isConditional: boolean): TGraphFace[] | undefined {
  if (isConditional && isCardNode(node)) {
    return CHECK_IF_FACES;
  }

  if (isCardNode(node)) {
    return STEM_CARD_FACES;
  }

  return undefined;
}

function checkIfApproach(from: IGraphNodeBox, to: IGraphNodeBox): { stacked: TGraphFace | null; side: TGraphFace } {
  const side: TGraphFace = from.centerX < to.centerX ? 'left' : 'right';

  if (from.bottom <= to.y) {
    return { stacked: 'top', side };
  }

  if (from.y >= to.bottom) {
    return { stacked: 'bottom', side };
  }

  return { stacked: null, side };
}

function stemCardFace(node: TGraphNode, peer: TGraphNode, role: 'source' | 'target'): TGraphFace {
  const from = getGraphNodeBox(role === 'source' ? node : peer);
  const to = getGraphNodeBox(role === 'source' ? peer : node);

  if (role === 'source') {
    return to.centerY >= from.centerY ? 'bottom' : 'top';
  }

  return from.centerY <= to.centerY ? 'top' : 'bottom';
}

function checkIfFaces(
  source: TGraphNode,
  target: TGraphNode,
  laneSide?: 'left' | 'right',
): { source: TGraphFace; target: TGraphFace } {
  const from = getGraphNodeBox(source);
  const to = getGraphNodeBox(target);

  if (isJunctionNode(target) && isCardNode(source)) {
    const sourceFace: TGraphFace = to.centerX < from.centerX - GRAPH_EDGE_SIDEWAYS_THRESHOLD
      ? 'left'
      : 'right';
    const approach = checkIfApproach(from, to);

    return { source: sourceFace, target: approach.stacked ?? approach.side };
  }

  if (isJunctionNode(source) && isCardNode(target)) {
    const targetFace: TGraphFace = from.centerX <= to.centerX ? 'left' : 'right';
    const sourceFace: TGraphFace = targetFace === 'left' ? 'right' : 'left';

    return { source: sourceFace, target: targetFace };
  }

  const sameColumn = Boolean(laneSide) || sharesStemX(from, to);

  if (sameColumn) {
    let side: TGraphFace = 'right';
    if (laneSide === 'left' || (!laneSide && to.centerX < from.centerX - GRAPH_EDGE_SIDEWAYS_THRESHOLD)) {
      side = 'left';
    }

    return { source: side, target: side };
  }

  if (to.centerX >= from.centerX) {
    return { source: 'right', target: 'left' };
  }

  return { source: 'left', target: 'right' };
}

function grayFace(node: TGraphNode, peer: TGraphNode, role: 'source' | 'target', preferred: TGraphFace): TGraphFace {
  if (isCardNode(node)) {
    return stemCardFace(node, peer, role);
  }

  return preferred;
}

function pickFreeHandle(
  taken: Set<string>,
  nodeId: string,
  role: 'source' | 'target',
  preferred: TGraphFace[],
  allowed?: TGraphFace[],
): string {
  const pool = allowed ?? FACE_FALLBACK;
  const seen = new Set<TGraphFace>();
  const order = [...preferred, ...pool].filter((face) => {
    if (seen.has(face) || !pool.includes(face)) {
      return false;
    }

    seen.add(face);

    return true;
  });
  const face = order.find((item) => !taken.has(`${nodeId}|${handleForFace(role, item)}`)) ?? order[0];
  const handle = handleForFace(role, face);
  taken.add(`${nodeId}|${handle}`);

  return handle;
}

interface IBranchItem {
  id: string;
  dx: number;
  stackedFace: TGraphFace | null;
  sideFace: TGraphFace;
}

function firstOpenFace(preferred: TGraphFace, used: Set<TGraphFace>): TGraphFace {
  const seen = new Set<TGraphFace>();
  const order = [preferred, ...FACE_FALLBACK].filter((face) => {
    if (seen.has(face)) {
      return false;
    }

    seen.add(face);

    return true;
  });

  return order.find((face) => !used.has(face)) ?? preferred;
}

function assignJunctionBranchFaces(
  items: IBranchItem[],
  blocked: TGraphFace[] = [],
): Map<string, TGraphFace> {
  const stacked = items.filter((item) => item.stackedFace);
  const side = items.filter((item) => !item.stackedFace);
  const faces = new Map<string, TGraphFace>();
  const used = new Set<TGraphFace>(blocked);

  const take = (id: string, preferred: TGraphFace) => {
    const face = firstOpenFace(preferred, used);
    used.add(face);
    faces.set(id, face);
  };

  if (stacked.length <= 1) {
    stacked.forEach((item) => {
      if (item.stackedFace) {
        take(item.id, item.stackedFace);
      }
    });
  } else {
    const closest = stacked.reduce((best, item) => (
      Math.abs(item.dx) < Math.abs(best.dx) ? item : best
    ));

    stacked.forEach((item) => {
      if (item.id === closest.id && item.stackedFace) {
        take(item.id, item.stackedFace);

        return;
      }

      take(item.id, item.dx < 0 ? 'left' : 'right');
    });
  }

  const sideFaces = assignOppositeSides(side.map((item) => ({ id: item.id, dx: item.dx })));
  side.forEach((item) => {
    take(item.id, sideFaces.get(item.id) ?? item.sideFace);
  });

  return faces;
}

export function assignEdgeHandles(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, IEdgeHandles> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const handles = new Map<string, IEdgeHandles>();
  const taken = new Set<string>();

  const putHandles = (
    edge: TGraphEdge,
    source: TGraphNode,
    target: TGraphNode,
    preferredSource: TGraphFace,
    preferredTarget: TGraphFace,
  ) => {
    const isConditional = isConditionalGraphEdge(edge);
    let sourceFace = preferredSource;
    let targetFace = preferredTarget;

    if (isConditional) {
      const faces = checkIfFaces(source, target, edge.data?.laneSide);
      sourceFace = isCardNode(source) ? faces.source : preferredSource;
      targetFace = isCardNode(target) ? faces.target : preferredTarget;
    } else {
      sourceFace = grayFace(source, target, 'source', preferredSource);
      targetFace = grayFace(target, source, 'target', preferredTarget);
    }

    const sourceHandle = pickFreeHandle(taken, source.id, 'source', [sourceFace], allowedFaces(source, isConditional));
    const targetHandle = pickFreeHandle(taken, target.id, 'target', [targetFace], allowedFaces(target, isConditional));

    if (isJunctionNode(source)) {
      taken.add(`${source.id}|${sourceHandle.replace('source-', 'target-')}`);
    }

    if (isJunctionNode(target)) {
      taken.add(`${target.id}|${targetHandle.replace('target-', 'source-')}`);
    }

    handles.set(edge.id, {
      sourceHandle,
      targetHandle,
    });
  };

  edges.forEach((edge) => {
    if (!isLaneRoutedGraphEdge(edge)) {
      return;
    }

    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return;
    }

    const side: TGraphFace = edge.data?.laneSide === 'left' ? 'left' : 'right';
    putHandles(edge, source, target, side, side);
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'fork') {
      return;
    }

    const outgoing = edges.filter((edge) => (
      edge.source === node.id && !handles.has(edge.id) && !isConditionalGraphEdge(edge)
    ));
    const originX = getGraphNodeBox(node).centerX;
    const sourceFaces = assignJunctionBranchFaces(
      outgoing.flatMap((edge) => {
        const target = nodeById.get(edge.target);
        if (!target) {
          return [];
        }

        const preferred = preferredFaces(node, target);
        const dx = getGraphNodeBox(target).centerX - originX;

        return [{
          id: edge.id,
          dx,
          stackedFace: isStackedFace(preferred.source) ? preferred.source : null,
          sideFace: dx < 0 ? 'left' : 'right',
        }];
      }),
    );

    outgoing.forEach((edge) => {
      const target = nodeById.get(edge.target);
      if (!target) {
        return;
      }

      putHandles(
        edge,
        node,
        target,
        sourceFaces.get(edge.id) ?? preferredFaces(node, target).source,
        preferredFaces(node, target).target,
      );
    });
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'join') {
      return;
    }

    const incoming = edges.filter((edge) => (
      edge.target === node.id
      && !handles.has(edge.id)
      && !isLaneRoutedGraphEdge(edge)
      && !isConditionalGraphEdge(edge)
    ));
    const originX = getGraphNodeBox(node).centerX;
    const targetFaces = assignJunctionBranchFaces(
      incoming.flatMap((edge) => {
        const source = nodeById.get(edge.source);
        if (!source) {
          return [];
        }

        const preferred = preferredFaces(source, node);
        const dx = getGraphNodeBox(source).centerX - originX;

        return [{
          id: edge.id,
          dx,
          stackedFace: isStackedFace(preferred.target) ? preferred.target : null,
          sideFace: dx < 0 ? 'left' : 'right',
        }];
      }),
    );

    incoming.forEach((edge) => {
      const source = nodeById.get(edge.source);
      if (!source) {
        return;
      }

      putHandles(
        edge,
        source,
        node,
        preferredFaces(source, node).source,
        targetFaces.get(edge.id) ?? preferredFaces(source, node).target,
      );
    });
  });

  const checkIfStemFace = new Map<string, TGraphFace>();

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'fork' || !isCheckIfJunctionId(node.id)) {
      return;
    }

    const inbound = edges.find((edge) => (
      edge.target === node.id && !handles.has(edge.id) && isConditionalGraphEdge(edge)
    ));
    const card = inbound ? nodeById.get(inbound.source) : undefined;

    if (inbound && card) {
      const faces = checkIfFaces(card, node);
      putHandles(inbound, card, node, faces.source, faces.target);
      const assigned = handles.get(inbound.id);

      if (assigned) {
        checkIfStemFace.set(node.id, faceFromHandle(assigned.targetHandle));
      }
    }
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'join' || !isCheckIfJunctionId(node.id)) {
      return;
    }

    const outbound = edges.find((edge) => (
      edge.source === node.id && !handles.has(edge.id) && isConditionalGraphEdge(edge)
    ));
    const card = outbound ? nodeById.get(outbound.target) : undefined;

    if (outbound && card) {
      const faces = checkIfFaces(node, card);
      putHandles(outbound, node, card, faces.source, faces.target);
      const assigned = handles.get(outbound.id);

      if (assigned) {
        checkIfStemFace.set(node.id, faceFromHandle(assigned.sourceHandle));
      }
    }
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'fork' || !isCheckIfJunctionId(node.id)) {
      return;
    }

    const outgoing = edges.filter((edge) => (
      edge.source === node.id && !handles.has(edge.id) && isConditionalGraphEdge(edge)
    ));
    const originX = getGraphNodeBox(node).centerX;
    const blocked = checkIfStemFace.get(node.id);
    const sourceFaces = assignJunctionBranchFaces(
      outgoing.flatMap((edge) => {
        const target = nodeById.get(edge.target);
        if (!target) {
          return [];
        }

        const dx = getGraphNodeBox(target).centerX - originX;
        const fromBox = getGraphNodeBox(node);
        const toBox = getGraphNodeBox(target);
        let stackedFace: TGraphFace | null = null;
        if (toBox.y >= fromBox.bottom) {
          stackedFace = 'bottom';
        } else if (toBox.bottom <= fromBox.y) {
          stackedFace = 'top';
        }

        return [{
          id: edge.id,
          dx,
          stackedFace,
          sideFace: dx < 0 ? 'left' : 'right',
        }];
      }),
      blocked ? [blocked] : [],
    );

    outgoing.forEach((edge) => {
      const target = nodeById.get(edge.target);
      if (!target) {
        return;
      }

      putHandles(
        edge,
        node,
        target,
        sourceFaces.get(edge.id) ?? checkIfFaces(node, target).source,
        checkIfFaces(node, target).target,
      );
    });
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'join' || !isCheckIfJunctionId(node.id)) {
      return;
    }

    const incoming = edges.filter((edge) => (
      edge.target === node.id && !handles.has(edge.id) && isConditionalGraphEdge(edge)
    ));
    const originX = getGraphNodeBox(node).centerX;
    const blocked = checkIfStemFace.get(node.id);
    const targetFaces = assignJunctionBranchFaces(
      incoming.flatMap((edge) => {
        const source = nodeById.get(edge.source);
        if (!source) {
          return [];
        }

        const dx = getGraphNodeBox(source).centerX - originX;
        const approach = checkIfApproach(getGraphNodeBox(source), getGraphNodeBox(node));

        return [{
          id: edge.id,
          dx,
          stackedFace: approach.stacked,
          sideFace: approach.side,
        }];
      }),
      blocked ? [blocked] : [],
    );

    incoming.forEach((edge) => {
      const source = nodeById.get(edge.source);
      if (!source) {
        return;
      }

      putHandles(
        edge,
        source,
        node,
        checkIfFaces(source, node).source,
        targetFaces.get(edge.id) ?? checkIfFaces(source, node).target,
      );
    });
  });

  edges.forEach((edge) => {
    if (handles.has(edge.id)) {
      return;
    }

    const source = nodeById.get(edge.source);
    const target = nodeById.get(edge.target);

    if (!source || !target) {
      return;
    }

    const faces = preferredFaces(source, target);
    putHandles(edge, source, target, faces.source, faces.target);
  });

  return handles;
}
