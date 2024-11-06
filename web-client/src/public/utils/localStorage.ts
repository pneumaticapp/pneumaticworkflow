import { WORKFLOW_VIEW_STATE_STORAGE_KEY } from "./workflows/filters";

export function removeLocalStorage() {
  const REMOVE_STORAGE_LIST = [
    WORKFLOW_VIEW_STATE_STORAGE_KEY,
  ];

  REMOVE_STORAGE_LIST.forEach(key => localStorage.removeItem(key));
}
