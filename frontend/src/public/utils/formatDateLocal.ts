/**
 * Formats a Date object to a local YYYY-MM-DD string without timezone shifts.
 * Returns null if the input date is null.
 */
export const formatDateLocal = (date: Date | null): string | null => {
  if (!date) return null;
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};
