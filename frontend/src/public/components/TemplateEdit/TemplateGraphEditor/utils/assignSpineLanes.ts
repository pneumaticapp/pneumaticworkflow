import { EGraphNodeType, TGraphEdge, TGraphNode } from '../types';
import { isConditionalGraphEdge } from './edgeStyles';
import { getJunctionKind, isCardNode } from './graphGeometry';

function resolveCheckIfCard(
  id: string,
  nodeById: Map<string, TGraphNode>,
  edges: TGraphEdge[],
): string {
  const node = nodeById.get(id);

  if (node && isCardNode(node)) {
    return id;
  }

  const stemOut = edges.find((edge) => edge.source === id && !isConditionalGraphEdge(edge));
  const stemTarget = stemOut ? nodeById.get(stemOut.target) : undefined;

  if (stemOut && stemTarget && isCardNode(stemTarget)) {
    return stemOut.target;
  }

  const inbound = edges.find((edge) => edge.target === id);
  const inboundSource = inbound ? nodeById.get(inbound.source) : undefined;

  if (inbound && inboundSource && isCardNode(inboundSource)) {
    return inbound.source;
  }

  return id;
}

function buildCheckIfPartners(nodes: TGraphNode[], edges: TGraphEdge[]): Map<string, string[]> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const partners = new Map<string, string[]>();

  const link = (from: string, to: string) => {
    if (from === to) {
      return;
    }

    const list = partners.get(from) ?? [];
    list.push(to);
    partners.set(from, list);
  };

  edges.forEach((edge) => {
    if (!isConditionalGraphEdge(edge)) {
      return;
    }

    const from = resolveCheckIfCard(edge.source, nodeById, edges);
    const to = resolveCheckIfCard(edge.target, nodeById, edges);
    link(from, to);
    link(to, from);
  });

  return partners;
}

function buildAdjacency(nodes: TGraphNode[], edges: TGraphEdge[]) {
  const successors = new Map<string, string[]>();
  const predecessors = new Map<string, string[]>();

  nodes.forEach((node) => {
    successors.set(node.id, []);
    predecessors.set(node.id, []);
  });

  edges.forEach((edge) => {
    successors.get(edge.source)?.push(edge.target);
    predecessors.get(edge.target)?.push(edge.source);
  });

  return { successors, predecessors };
}

function getSortNumber(node: TGraphNode | undefined): number {
  if (!node) {
    return Number.MAX_SAFE_INTEGER;
  }

  if (node.type === EGraphNodeType.Task) {
    return node.data.task.number;
  }

  if (node.type === EGraphNodeType.Kickoff) {
    return -1;
  }

  return Number.MAX_SAFE_INTEGER;
}

export function assignSpineLanes(
  nodes: TGraphNode[],
  edges: TGraphEdge[],
  levels: Map<string, number>,
): Map<string, number> {
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const stemEdges = edges.filter((edge) => !isConditionalGraphEdge(edge));
  const checkIfPartners = buildCheckIfPartners(nodes, edges);
  const { successors, predecessors } = buildAdjacency(nodes, stemEdges);
  const depthMemo = new Map<string, number>();

  const remainingCards = (id: string, visiting: Set<string> = new Set()): number => {
    const cached = depthMemo.get(id);
    if (cached != null) {
      return cached;
    }

    if (visiting.has(id)) {
      return 0;
    }

    visiting.add(id);
    const node = nodeById.get(id);
    const self = node && isCardNode(node) ? 1 : 0;
    const kids = successors.get(id) ?? [];
    const next = kids.reduce((max, kid) => Math.max(max, remainingCards(kid, visiting)), 0);
    visiting.delete(id);
    const value = self + next;
    depthMemo.set(id, value);

    return value;
  };

  nodes.forEach((node) => {
    remainingCards(node.id);
  });

  const compareIds = (first: string, second: string): number => {
    const depthDiff = remainingCards(second) - remainingCards(first);
    if (depthDiff !== 0) {
      return depthDiff;
    }

    const numberDiff = getSortNumber(nodeById.get(first)) - getSortNumber(nodeById.get(second));
    if (numberDiff !== 0) {
      return numberDiff;
    }

    return first.localeCompare(second);
  };

  const pickMainSuccessor = (id: string): string | undefined => {
    const kids = [...(successors.get(id) ?? [])].sort(compareIds);

    return kids[0];
  };

  const buildTrunk = (startId: string): string[] => {
    const path: string[] = [];
    const seen = new Set<string>();
    let current: string | undefined = startId;

    while (current && !seen.has(current)) {
      seen.add(current);
      path.push(current);
      current = pickMainSuccessor(current);
    }

    return path;
  };

  const occupied = new Map<number, Set<number>>();
  const lanes = new Map<string, number>();

  const isFree = (lane: number, level: number): boolean => !(occupied.get(lane)?.has(level) ?? false);

  const occupy = (lane: number, level: number) => {
    const levelsAtLane = occupied.get(lane) ?? new Set<number>();
    levelsAtLane.add(level);
    occupied.set(lane, levelsAtLane);
  };

  const setLane = (id: string, lane: number) => {
    lanes.set(id, lane);
    const node = nodeById.get(id);

    if (node && isCardNode(node)) {
      occupy(lane, levels.get(id) ?? 0);
    }
  };

  const collectOpenLanes = (origin: number, level: number, dir: -1 | 1): number[] => {
    const found: number[] = [];
    const limit = origin + dir * (nodes.length + 4);

    for (let lane = origin + dir; dir < 0 ? lane >= limit : lane <= limit; lane += dir) {
      if (!isFree(lane, level)) {
        break;
      }

      found.push(lane);
    }

    return found;
  };

  const takeFallbackLane = (origin: number, level: number, dir: -1 | 1): number => {
    const limit = origin + dir * (nodes.length + 8);

    for (let lane = origin + dir; dir < 0 ? lane >= limit : lane <= limit; lane += dir) {
      if (isFree(lane, level)) {
        return lane;
      }
    }

    return origin + dir;
  };

  const sideOfLane = (lane: number): 'left' | 'right' | 'both' => {
    if (lane < 0) {
      return 'left';
    }

    if (lane > 0) {
      return 'right';
    }

    return 'both';
  };

  const assignExtraLanes = (
    origin: number,
    level: number,
    ordered: string[],
    side: 'left' | 'right' | 'both',
  ) => {
    const leftSlots = side === 'right' ? [] : collectOpenLanes(origin, level, -1);
    const rightSlots = side === 'left' ? [] : collectOpenLanes(origin, level, 1);
    let leftIndex = 0;
    let rightIndex = 0;

    const takeLeft = (): number | undefined => {
      if (leftIndex >= leftSlots.length) {
        return undefined;
      }

      const lane = leftSlots[leftIndex];
      leftIndex += 1;

      return lane;
    };

    const takeRight = (): number | undefined => {
      if (rightIndex >= rightSlots.length) {
        return undefined;
      }

      const lane = rightSlots[rightIndex];
      rightIndex += 1;

      return lane;
    };

    ordered.forEach((id, index) => {
      const partnerPull = (checkIfPartners.get(id) ?? []).reduce((sum, partnerId) => {
        if (!lanes.has(partnerId)) {
          return sum;
        }

        return sum + ((lanes.get(partnerId) ?? 0) - origin);
      }, 0);
      let preferLeft = side === 'left' || (side === 'both' && index % 2 === 0);

      if (side === 'both' && partnerPull > 0) {
        preferLeft = false;
      }

      if (side === 'both' && partnerPull < 0) {
        preferLeft = true;
      }
      const preferred = preferLeft ? takeLeft() : takeRight();
      let other: number | undefined;

      if (preferred == null) {
        other = preferLeft ? takeRight() : takeLeft();
      }

      let fallbackDir: -1 | 1 = -1;
      if (side === 'right' || (!preferLeft && side === 'both')) {
        fallbackDir = 1;
      }

      setLane(id, preferred ?? other ?? takeFallbackLane(origin, level, fallbackDir));
    });
  };

  const compareBranchesShortFirst = (first: string, second: string): number => {
    const lengthDiff = remainingCards(first) - remainingCards(second);
    if (lengthDiff !== 0) {
      return lengthDiff;
    }

    const numberDiff = getSortNumber(nodeById.get(first)) - getSortNumber(nodeById.get(second));
    if (numberDiff !== 0) {
      return numberDiff;
    }

    return first.localeCompare(second);
  };

  const compareExtras = (first: string, second: string): number => {
    const placedLinks = (id: string): number => (
      (checkIfPartners.get(id) ?? []).filter((partnerId) => lanes.has(partnerId)).length
    );
    const linkDiff = placedLinks(second) - placedLinks(first);

    if (linkDiff !== 0) {
      return linkDiff;
    }

    return compareBranchesShortFirst(first, second);
  };

  const roots = nodes
    .map((node) => node.id)
    .filter((id) => (predecessors.get(id) ?? []).length === 0)
    .sort(compareIds);
  const primaryRoot = roots.includes('kickoff') ? 'kickoff' : roots[0];

  if (primaryRoot) {
    buildTrunk(primaryRoot).forEach((id) => setLane(id, 0));
  }

  roots.forEach((rootId) => {
    if (lanes.has(rootId)) {
      return;
    }

    assignExtraLanes(0, levels.get(rootId) ?? 0, [rootId], 'both');
    const lane = lanes.get(rootId) ?? -1;
    buildTrunk(rootId).forEach((id) => {
      if (!lanes.has(id)) {
        setLane(id, lane);
      }
    });
  });

  const topo = [...nodes]
    .sort((first, second) => {
      const levelDiff = (levels.get(first.id) ?? 0) - (levels.get(second.id) ?? 0);
      if (levelDiff !== 0) {
        return levelDiff;
      }

      return compareIds(first.id, second.id);
    })
    .map((node) => node.id);

  const sortParents = (first: string, second: string): number => {
    const depthDiff = remainingCards(second) - remainingCards(first);
    if (depthDiff !== 0) {
      return depthDiff;
    }

    return Math.abs(lanes.get(first) ?? 0) - Math.abs(lanes.get(second) ?? 0);
  };

  const isSyntheticCheckIfJoin = (id: string): boolean => {
    const node = nodeById.get(id);

    return Boolean(node && getJunctionKind(node) === 'join' && (predecessors.get(id) ?? []).length === 1);
  };

  const pickPlacedParent = (id: string): string | undefined => {
    const parentIds = (predecessors.get(id) ?? []).filter((parentId) => lanes.has(parentId));

    if (parentIds.length === 0) {
      return undefined;
    }

    parentIds.sort(sortParents);

    const parentId = parentIds[0];

    if (!parentId || !isSyntheticCheckIfJoin(parentId)) {
      return parentId;
    }

    const grandparentIds = (predecessors.get(parentId) ?? []).filter((grandId) => lanes.has(grandId));
    grandparentIds.sort(sortParents);

    return grandparentIds[0] ?? parentId;
  };

  const propagateJunctionLanes = () => {
    nodes.forEach((node) => {
      if (lanes.has(node.id) || isCardNode(node)) {
        return;
      }

      const parentId = pickPlacedParent(node.id);

      if (parentId) {
        setLane(node.id, lanes.get(parentId) ?? 0);
      }
    });
  };

  const remaining = topo.filter((id) => !lanes.has(id));
  const pendingCardIds = remaining.filter((id) => {
    const node = nodeById.get(id);

    return Boolean(node && isCardNode(node));
  });
  const remainingLevels = [...new Set(pendingCardIds.map((id) => levels.get(id) ?? 0))]
    .sort((first, second) => first - second);

  remainingLevels.forEach((level) => {
    propagateJunctionLanes();
    const ids = pendingCardIds.filter((id) => (levels.get(id) ?? 0) === level);

    ids.forEach((id) => {
      if (lanes.has(id)) {
        return;
      }

      const parentId = pickPlacedParent(id);

      if (!parentId) {
        return;
      }

      const parentLane = lanes.get(parentId) ?? 0;

      if (id === pickMainSuccessor(parentId) && isFree(parentLane, level)) {
        setLane(id, parentLane);
      }
    });

    const extras = ids.filter((id) => !lanes.has(id));
    const extrasByParent = new Map<string, string[]>();

    extras.forEach((id) => {
      const parentId = pickPlacedParent(id) ?? '__root__';
      const group = extrasByParent.get(parentId) ?? [];
      group.push(id);
      extrasByParent.set(parentId, group);
    });

    [...extrasByParent.entries()]
      .sort((first, second) => {
        const laneDiff = Math.abs(lanes.get(first[0]) ?? 0) - Math.abs(lanes.get(second[0]) ?? 0);
        if (laneDiff !== 0) {
          return laneDiff;
        }

        return (lanes.get(first[0]) ?? 0) - (lanes.get(second[0]) ?? 0);
      })
      .forEach(([parentId, group]) => {
        const ordered = [...group].sort(compareExtras);

        if (parentId === '__root__') {
          assignExtraLanes(0, level, ordered, 'both');

          return;
        }

        const parentLane = lanes.get(parentId) ?? 0;
        assignExtraLanes(parentLane, level, ordered, sideOfLane(parentLane));
      });
  });

  return lanes;
}
