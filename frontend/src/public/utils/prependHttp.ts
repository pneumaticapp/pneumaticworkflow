/* eslint-disable */
/* prettier-ignore */
type TPrependHttpConfig = {
  https?: boolean;
};

export function prependHttp(url: string, { https = true }: TPrependHttpConfig = {}) {
  const normalizedUrl = url.trim();

  if (/^\.*\/|^(?!localhost)\w+?:/.test(normalizedUrl)) {
    return normalizedUrl;
  }

  return normalizedUrl.replace(/^(?!(?:\w+?:)?\/\/)/, https ? 'https://' : 'http://');
}
