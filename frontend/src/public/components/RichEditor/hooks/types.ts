import type { RefObject } from 'react';
import type { IScrollSnapshot } from '../plugins/LinkPlugin/types';

export interface ISelectionAnchorResult {
  frozenRect: DOMRect | null;
  scrollSnapshots: IScrollSnapshot[];
  anchorElement: HTMLElement | null;
}

export interface IUseFloatingFormPositionOptions {
  anchorElement?: HTMLElement | null;
  containerRef?: RefObject<HTMLElement | null>;
  getAnchorRect?: (() => DOMRect | null) | null;
  isVisible: boolean;
  offsetPx?: number;
}

export interface IFloatingFormPosition {
  top: number;
  left: number;
}

export type TFloatingFormPositionMode = 'fixed' | 'absolute';

export interface IUseFloatingFormPositionResult {
  position: IFloatingFormPosition | null;
  positionMode: TFloatingFormPositionMode;
}
