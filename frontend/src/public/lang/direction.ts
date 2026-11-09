export type TLocaleDirection = 'ltr' | 'rtl';

export function isRtlLocale(locale: string): boolean {
  return locale.toLowerCase().split(/[-_]/)[0] === 'ar';
}

export function getLocaleDirection(locale: string): TLocaleDirection {
  return isRtlLocale(locale) ? 'rtl' : 'ltr';
}

/** Resolve physical Popper placements once at the shared component boundary. */
export function resolveDirectionalPlacement<T extends string>(placement: T, direction: TLocaleDirection): T {
  if (direction === 'ltr') return placement;
  const [side, alignment] = placement.split('-');
  if (side === 'left' || side === 'right') {
    return `${side === 'left' ? 'right' : 'left'}${alignment ? `-${alignment}` : ''}` as T;
  }
  if (alignment && (side === 'top' || side === 'bottom' || side === 'auto')) {
    return `${side}-${alignment === 'start' ? 'end' : 'start'}` as T;
  }
  return placement;
}
