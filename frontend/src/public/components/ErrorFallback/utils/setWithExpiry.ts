export function setWithExpiry(key: string, value: string, ttl: number) {
  const item = {
    value,
    expiry: new Date().getTime() + ttl,
  };
  localStorage.setItem(key, JSON.stringify(item));
}
