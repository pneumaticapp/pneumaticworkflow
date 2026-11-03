import { EGraphViewMode } from '../types';

export const GRAPH_VIEW_MODE_STORAGE_KEY = 'template_graph_view_mode';

function isGraphViewMode(value: unknown): value is EGraphViewMode {
  return value === EGraphViewMode.List || value === EGraphViewMode.Graph;
}

export function getGraphViewMode(): EGraphViewMode {
  if (typeof localStorage === 'undefined') {
    return EGraphViewMode.List;
  }

  try {
    const rawValue = localStorage.getItem(GRAPH_VIEW_MODE_STORAGE_KEY);

    return isGraphViewMode(rawValue) ? rawValue : EGraphViewMode.List;
  } catch {
    return EGraphViewMode.List;
  }
}

export function saveGraphViewMode(viewMode: EGraphViewMode): void {
  if (!isGraphViewMode(viewMode) || typeof localStorage === 'undefined') {
    return;
  }

  try {
    localStorage.setItem(GRAPH_VIEW_MODE_STORAGE_KEY, viewMode);
  } catch {
    // Storage can be unavailable because of browser privacy settings or quota limits.
  }
}
