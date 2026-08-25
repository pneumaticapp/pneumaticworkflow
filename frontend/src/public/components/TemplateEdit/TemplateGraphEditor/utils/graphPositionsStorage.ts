import { IGraphNodePosition, TGraphNodePositions, TGraphPositionsStorage } from '../types';

export const GRAPH_POSITIONS_STORAGE_KEY = 'template_graph_node_positions';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isGraphNodePosition(value: unknown): value is IGraphNodePosition {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.x === 'number'
    && Number.isFinite(value.x)
    && typeof value.y === 'number'
    && Number.isFinite(value.y)
  );
}

function parseNodePositions(value: unknown): TGraphNodePositions {
  if (!isRecord(value)) {
    return {};
  }

  return Object.entries(value).reduce<TGraphNodePositions>((positions, [nodeId, position]) => {
    if (isGraphNodePosition(position)) {
      positions[nodeId] = position;
    }

    return positions;
  }, {});
}

function readStorage(): TGraphPositionsStorage {
  if (typeof localStorage === 'undefined') {
    return {};
  }

  try {
    const rawValue = localStorage.getItem(GRAPH_POSITIONS_STORAGE_KEY);
    if (!rawValue) {
      return {};
    }

    const parsedValue: unknown = JSON.parse(rawValue);
    if (!isRecord(parsedValue)) {
      return {};
    }

    return Object.entries(parsedValue).reduce<TGraphPositionsStorage>((storage, [templateId, positions]) => {
      storage[templateId] = parseNodePositions(positions);

      return storage;
    }, {});
  } catch {
    return {};
  }
}

export function getGraphNodePositions(templateId?: number): TGraphNodePositions {
  if (templateId == null) {
    return {};
  }

  return readStorage()[String(templateId)] ?? {};
}

export function saveGraphNodePosition(
  templateId: number | undefined,
  nodeId: string,
  position: IGraphNodePosition,
): void {
  if (templateId == null || !isGraphNodePosition(position) || typeof localStorage === 'undefined') {
    return;
  }

  try {
    const storage = readStorage();
    const templateKey = String(templateId);

    storage[templateKey] = {
      ...storage[templateKey],
      [nodeId]: position,
    };

    localStorage.setItem(GRAPH_POSITIONS_STORAGE_KEY, JSON.stringify(storage));
  } catch {
    // Storage can be unavailable because of browser privacy settings or quota limits.
  }
}
