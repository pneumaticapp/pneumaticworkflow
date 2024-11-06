export function getUrlParams(search: string): {[key: string]: string} {
  const hashes = search.slice(search.indexOf('?') + 1).split('&');

  return hashes.reduce((params, hash) => {
    const [key, val] = hash.split('=');

    return Object.assign(params, {[key]: decodeURIComponent(val)});
  }, {});
}
