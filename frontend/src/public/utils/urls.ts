import { ALLOWED_PROTOCOLS, hostNameRegex } from '../constants/defaultValues';

export function mergePaths(left: string, right: string) {
  const leftSlash = left[left.length - 1] === '/';
  const rightSlash = right[0] === '/';
  if (leftSlash && rightSlash) {
    return `${left}${right.slice(1)}`;
  }
  if (!leftSlash && !rightSlash) {
    return `${left}/${right}`;
  }

  return `${left}${right}`;
}

export function getHostName(url: string, isDirect?: boolean) {
  const match = url.match(hostNameRegex);

  if (isDirect) {
    return url;
  }

  if (match && match.length > 0 && typeof match[3] === 'string') {
    return match[3];
  }

  return undefined;
}

export function isValidUri(value: string) {
  try {
    const { protocol } = new URL(value);
    return ALLOWED_PROTOCOLS.has(protocol);
  } catch {
    return false;
  }
}
