/**
 * Detects Safari browser for workarounds (e.g. selection/copy with inline decorators).
 * Chrome on iOS reports as Safari in some APIs; this targets desktop Safari and WebKit Safari.
 */
export function isSafari(): boolean {
  if (typeof navigator === 'undefined') {
    return false;
  }
  const ua = navigator.userAgent;
  const {vendor} = navigator;
  // Safari (desktop and iOS) but not Chrome (Chrome has "Chrome" in UA and "Google Inc." vendor)
  return (
    (vendor !== undefined && vendor.indexOf('Apple') !== -1 && ua.indexOf('CriOS') === -1) ||
    (ua.indexOf('Safari') !== -1 && ua.indexOf('Chrome') === -1)
  );
}
