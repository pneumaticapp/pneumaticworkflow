import { TGraphEdge, TGraphNode } from '../types';
import { isLaneRoutedGraphEdge } from './edgeStyles';
import {
  GRAPH_EDGE_SIDEWAYS_THRESHOLD,
  TGraphFace,
  getGraphNodeBox,
  getJunctionKind,
  handleForFace,
  preferredFaces,
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

interface IBranchItem {
  id: string;
  dx: number;
  stackedFace: TGraphFace | null;
  sideFace: TGraphFace;
}

function assignJunctionBranchFaces(items: IBranchItem[]): Map<string, TGraphFace> {
  const stacked = items.filter((item) => item.stackedFace);
  const side = items.filter((item) => !item.stackedFace);
  const faces = new Map<string, TGraphFace>();

  if (stacked.length <= 1) {
    stacked.forEach((item) => {
      if (item.stackedFace) {
        faces.set(item.id, item.stackedFace);
      }
    });
  } else {
    const closest = stacked.reduce((best, item) => (
      Math.abs(item.dx) < Math.abs(best.dx) ? item : best
    ));

    stacked.forEach((item) => {
      if (item.id === closest.id && item.stackedFace) {
        faces.set(item.id, item.stackedFace);

        return;
      }

      faces.set(item.id, item.dx < 0 ? 'left' : 'right');
    });
  }

  const sideFaces = assignOppositeSides(side.map((item) => ({ id: item.id, dx: item.dx })));
  side.forEach((item) => {
    faces.set(item.id, sideFaces.get(item.id) ?? item.sideFace);
  });

  return faces;
}

export function assignEdgeHandles(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, IEdgeHandles> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const handles = new Map<string, IEdgeHandles>();

  edges.forEach((edge) => {
    if (!isLaneRoutedGraphEdge(edge)) {
      return;
    }

    const side: TGraphFace = edge.data?.laneSide === 'left' ? 'left' : 'right';
    handles.set(edge.id, {
      sourceHandle: handleForFace('source', side),
      targetHandle: handleForFace('target', side),
    });
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'fork') {
      return;
    }

    const outgoing = edges.filter((edge) => edge.source === node.id && !handles.has(edge.id));
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

      const sourceFace = sourceFaces.get(edge.id) ?? preferredFaces(node, target).source;
      const targetFace = preferredFaces(node, target).target;

      handles.set(edge.id, {
        sourceHandle: handleForFace('source', sourceFace),
        targetHandle: handleForFace('target', targetFace),
      });
    });
  });

  nodes.forEach((node) => {
    if (getJunctionKind(node) !== 'join') {
      return;
    }

    const incoming = edges.filter((edge) => edge.target === node.id && !isLaneRoutedGraphEdge(edge));
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

      const targetHandle = handleForFace('target', targetFaces.get(edge.id) ?? preferredFaces(source, node).target);
      const existing = handles.get(edge.id);

      if (existing) {
        handles.set(edge.id, { ...existing, targetHandle });

        return;
      }

      handles.set(edge.id, {
        sourceHandle: handleForFace('source', preferredFaces(source, node).source),
        targetHandle,
      });
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
    handles.set(edge.id, {
      sourceHandle: handleForFace('source', faces.source),
      targetHandle: handleForFace('target', faces.target),
    });
  });

  return handles;
}
