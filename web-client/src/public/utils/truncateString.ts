import { ELLIPSIS_CHAR } from '../constants/defaultValues';

export function truncateString(str?: string, maxLength: number = 20) {
  if (!str || typeof str !== 'string') {
    return str;
  }

  if (str.length <= maxLength) {
    return str;
  }

  return str.slice(0, maxLength).trim() + ELLIPSIS_CHAR;
}
