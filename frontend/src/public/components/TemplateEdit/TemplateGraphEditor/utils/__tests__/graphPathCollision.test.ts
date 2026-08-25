import { EGraphNodeType, TGraphNode } from '../../types';
import {
  GRAPH_NODE_HEIGHT,
  GRAPH_NODE_WIDTH,
  GRAPH_ROW_GAP,
} from '../graphGeometry';
import { pickClearY, pickTreeGutterX, segmentCrowdsCard, segmentHitsCard } from '../graphPathCollision';

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

describe('graphPathCollision', () => {
  it('should treat a line through the card body as a hit and a line on the border as a miss', () => {
    const blocker = card('blocker', 0, 0);

    expect(segmentHitsCard({ a: { x: 40, y: 40 }, b: { x: 200, y: 40 } }, blocker)).toBe(true);
    expect(segmentHitsCard({ a: { x: 40, y: 0 }, b: { x: 200, y: 0 } }, blocker)).toBe(false);
  });

  it('should treat a line just under a card as crowding it', () => {
    const blocker = card('blocker', 0, 0);

    expect(segmentCrowdsCard(
      { a: { x: 40, y: GRAPH_NODE_HEIGHT + 8 }, b: { x: 200, y: GRAPH_NODE_HEIGHT + 8 } },
      blocker,
    )).toBe(true);
  });

  it('should pick a row gap above a blocking card, not a line under it', () => {
    const y = pickClearY(40, 400, 80, [card('blocker', 80, 40)], new Set(), []);

    expect(y).toBeLessThan(40);
    expect(y).toBeGreaterThan(40 - GRAPH_ROW_GAP * 2);
  });

  it('should turn in the column gutter before the obstacle, not past it', () => {
    const x = pickTreeGutterX(40, 400, 80, [card('blocker', 120, 40)], new Set(), []);

    expect(x).toBeGreaterThan(40);
    expect(x).toBeLessThan(120);
  });

  it('should pick the local row gap, not a corridor above the whole tree', () => {
    const y = pickClearY(
      856,
      1484,
      776,
      [
        card('kickoff', 444, 0),
        card('mid', 888, 600),
        card('side', 888, 776),
        card('far', 1332, 776),
      ],
      new Set(['far']),
      [],
    );

    expect(y).toBeGreaterThan(600 + GRAPH_NODE_HEIGHT);
    expect(y).toBeLessThan(776);
  });
});
