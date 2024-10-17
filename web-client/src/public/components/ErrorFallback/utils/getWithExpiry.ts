export function getWithExpiry(key: string) {
  const itemString = window.localStorage.getItem(key);
  if (!itemString) {
    return null;
  }

  const item = JSON.parse(itemString);
  const isExpired = new Date().getTime() > item.expiry;

  if (isExpired) {
    localStorage.removeItem(key);

    return null;
  }

  return item.value;
}
