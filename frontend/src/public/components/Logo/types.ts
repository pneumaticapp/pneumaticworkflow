export type TLogoTheme = 'dark' | 'light';
export type TLogoSize = 'sm' | 'md' | 'lg';
export type TMinimizedLogoSize = 'sm' | 'md';
export type TExtendedLogoSize = 'lg';

export interface ILogoProps {
  size: TLogoSize;
  theme: TLogoTheme;
  partnerLogoSm: string | null;
  partnerLogoLg: string | null;
  className?: string;
}

export interface ILogoCircleProps {
  size?: number;
  theme?: TLogoTheme;
  className?: string;
}
