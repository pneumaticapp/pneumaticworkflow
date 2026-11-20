export type TSkeletonTheme = 'white' | 'beige';

export interface ISkeletonLoaderProps {
  display?: string;
  width?: string | number;
  height?: string | number;
  margin?: string;
  borderRadius?: string | number;
  className?: string;
  theme?: TSkeletonTheme;
}
