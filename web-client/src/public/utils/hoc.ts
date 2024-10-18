import * as React from 'react';

export function getDisplayName(WrappedComponent: React.ComponentType) {
  return WrappedComponent.displayName || WrappedComponent.name || 'Component';
}

export function getWrappedDisplayName(Component: React.ComponentType, hocName: string): string {
  return `${hocName}(${getDisplayName(Component)})`;
}
