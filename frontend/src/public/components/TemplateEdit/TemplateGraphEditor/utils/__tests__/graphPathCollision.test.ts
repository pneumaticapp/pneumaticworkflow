import { EGraphNodeType, TGraphNode } from '../../types';
import { GRAPH_NODE_HEIGHT, GRAPH_NODE_WIDTH, GRAPH_ROW_GAP, GRAPH_SKIP_LANE_STEP } from '../graphGeometry';
import {
  ILaneReservation,
  pickClearY,
  pickTreeGutterX,
  segmentCrowdsCard,
  segmentHitsCard,
} from '../graphPathCollision';

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

    expect(
      segmentCrowdsCard({ a: { x: 40, y: GRAPH_NODE_HEIGHT + 8 }, b: { x: 200, y: GRAPH_NODE_HEIGHT + 8 } }, blocker),
    ).toBe(true);
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
      [card('kickoff', 444, 0), card('mid', 888, 600), card('side', 888, 776), card('far', 1332, 776)],
      new Set(['far']),
      [],
    );

    expect(y).toBeGreaterThan(600 + GRAPH_NODE_HEIGHT);
    expect(y).toBeLessThan(776);
  });

  it('should step off a taken alley y even when no card sits on the span', () => {
    const y = pickClearY(40, 400, 80, [], new Set(), [{ at: 80, from: 40, to: 400 }]);

    expect(y).not.toBeNull();
    expect(Math.abs((y as number) - 80)).toBeGreaterThanOrEqual(GRAPH_SKIP_LANE_STEP);
  });

  it('should reuse a taken alley y where the two runs do not overlap', () => {
    const y = pickClearY(40, 400, 80, [], new Set(), [{ at: 80, from: 800, to: 1200 }]);

    expect(y).toBe(80);
  });

  it('should pack several alleys into one row gap instead of leaving the tree', () => {
    const cards = [card('top', 0, 0), card('bottom', 0, GRAPH_NODE_HEIGHT + GRAPH_ROW_GAP)];
    const gapTop = GRAPH_NODE_HEIGHT;
    const gapBottom = GRAPH_NODE_HEIGHT + GRAPH_ROW_GAP;
    const taken: ILaneReservation[] = [];

    [1, 2].forEach(() => {
      const y = pickClearY(40, 400, gapTop + GRAPH_ROW_GAP / 2, cards, new Set(), taken);

      expect(y).not.toBeNull();
      expect(y as number).toBeGreaterThan(gapTop);
      expect(y as number).toBeLessThan(gapBottom);
      taken.push({ at: y as number, from: 40, to: 400 });
    });
  });
});
