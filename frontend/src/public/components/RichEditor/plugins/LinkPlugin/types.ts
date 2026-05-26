export type TLinkFormMode = 'create-link-at-selection' | 'create-link-from-scratch';

export interface ILinkPluginContextValue {
  openLinkForm: (
    rect: DOMRect | null,
    mode: TLinkFormMode,
    buttonRef: React.RefObject<HTMLButtonElement | null>,
  ) => void;
  closeLinkForm: () => void;
  applyLink: (url: string, linkText?: string) => void;
}

export interface ILinkFormState {
  isOpen: boolean;
  anchorRect: DOMRect | null;
  anchorElement: HTMLElement | null;
  getAnchorRect: (() => DOMRect | null) | null;
  formMode: TLinkFormMode;
}

export interface IScrollSnapshot {
  element: Element;
  scrollLeft: number;
  scrollTop: number;
}
