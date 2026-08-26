import { EGraphNodeType, TGraphNode } from '../../types';
import {
  GRAPH_JUNCTION_SIZE,
  GRAPH_NODE_HEIGHT,
  GRAPH_NODE_WIDTH,
  getHandleAnchor,
  offsetAlongFace,
  preferredFaces,
  snapOutOfStandoffStrip,
} from '../graphGeometry';

function card(id: string, x: number, y: number): TGraphNode {
  return {
    id,
    type: EGraphNodeType.Task,
    position: { x, y },
    width: GRAPH_NODE_WIDTH,
    height: GRAPH_NODE_HEIGHT,
    data: {},
  } as TGraphNode;
}

function junction(id: string, x: number, y: number, kind: 'fork' | 'join'): TGraphNode {
  return {
    id,
    type: EGraphNodeType.Junction,
    position: { x, y },
    width: GRAPH_JUNCTION_SIZE,
    height: GRAPH_JUNCTION_SIZE,
    data: { kind },
  };
}

describe('offsetAlongFace', () => {
  it('should move a point out of the card along the given face', () => {
    expect(offsetAlongFace({ x: 10, y: 20 }, 'right', 10)).toEqual({ x: 20, y: 20 });
    expect(offsetAlongFace({ x: 10, y: 20 }, 'left', 10)).toEqual({ x: 0, y: 20 });
    expect(offsetAlongFace({ x: 10, y: 20 }, 'top', 10)).toEqual({ x: 10, y: 10 });
    expect(offsetAlongFace({ x: 10, y: 20 }, 'bottom', 10)).toEqual({ x: 10, y: 30 });
  });
});

describe('snapOutOfStandoffStrip', () => {
  it('should push a coordinate on the handle out to the standoff', () => {
    expect(snapOutOfStandoffStrip(200, 200, 168)).toBe(168);
  });

  it('should push a coordinate inside the strip out to the standoff', () => {
    expect(snapOutOfStandoffStrip(190, 200, 168)).toBe(168);
    expect(snapOutOfStandoffStrip(210, 200, 232)).toBe(232);
  });

  it('should keep a coordinate already on the standoff or outside it', () => {
    expect(snapOutOfStandoffStrip(168, 200, 168)).toBe(168);
    expect(snapOutOfStandoffStrip(40, 200, 168)).toBe(40);
  });
});

describe('preferredFaces', () => {
  it('should keep a stacked successor on the top and bottom', () => {
    expect(preferredFaces(card('a', 0, 0), card('b', 0, 200))).toEqual({
      source: 'bottom',
      target: 'top',
    });
  });

  it('should drop an offset fork child onto the top of the card', () => {
    expect(preferredFaces(junction('fork', 40, 40, 'fork'), card('task-6', 280, 160))).toEqual({
      source: 'right',
      target: 'top',
    });
  });

  it('should leave a junction sideways when the card is off the stem', () => {
    expect(preferredFaces(junction('fork', 148, 200, 'fork'), card('task-6', 280, 40))).toEqual({
      source: 'right',
      target: 'bottom',
    });
  });

  it('should keep stacked cards on top and bottom even when they only overlap in x', () => {
    expect(preferredFaces(card('a', 0, 0), card('b', 80, 200))).toEqual({
      source: 'bottom',
      target: 'top',
    });
  });

  it('should leave a card from the bottom when joining below', () => {
    expect(preferredFaces(card('b', 0, 0), junction('join', 400, 200, 'join'))).toEqual({
      source: 'bottom',
      target: 'top',
    });
  });

  it('should leave a card sideways into a neighbour on the same row', () => {
    expect(preferredFaces(card('a', 0, 0), card('b', 420, 0))).toEqual({
      source: 'right',
      target: 'left',
    });
  });
});

describe('getHandleAnchor', () => {
  it('should pin the line to the matching face of the card', () => {
    const node = card('task', 40, 80);

    expect(getHandleAnchor(node, 'source-top')).toEqual({ x: 40 + GRAPH_NODE_WIDTH / 2, y: 80 });
    expect(getHandleAnchor(node, 'source-bottom')).toEqual({
      x: 40 + GRAPH_NODE_WIDTH / 2,
      y: 80 + GRAPH_NODE_HEIGHT,
    });
    expect(getHandleAnchor(node, 'target-left')).toEqual({ x: 40, y: 80 + GRAPH_NODE_HEIGHT / 2 });
    expect(getHandleAnchor(node, 'source-right')).toEqual({
      x: 40 + GRAPH_NODE_WIDTH,
      y: 80 + GRAPH_NODE_HEIGHT / 2,
    });
  });

  it('should meet every junction line at the centre', () => {
    const node = junction('fork', 40, 80, 'fork');

    expect(getHandleAnchor(node, 'source-left')).toEqual({
      x: 40 + GRAPH_JUNCTION_SIZE / 2,
      y: 80 + GRAPH_JUNCTION_SIZE / 2,
    });
    expect(getHandleAnchor(node, 'target-top')).toEqual({
      x: 40 + GRAPH_JUNCTION_SIZE / 2,
      y: 80 + GRAPH_JUNCTION_SIZE / 2,
    });
    expect(getHandleAnchor(node, 'source-bottom')).toEqual({
      x: 40 + GRAPH_JUNCTION_SIZE / 2,
      y: 80 + GRAPH_JUNCTION_SIZE / 2,
    });
  });
});
