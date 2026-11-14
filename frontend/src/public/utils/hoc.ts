import type { ComponentType } from 'react';

export function getDisplayName(WrappedComponent: ComponentType) {
  return WrappedComponent.displayName || WrappedComponent.name || 'Component';
}

export function getWrappedDisplayName(Component: ComponentType, hocName: string): string {
  return `${hocName}(${getDisplayName(Component)})`;
}
