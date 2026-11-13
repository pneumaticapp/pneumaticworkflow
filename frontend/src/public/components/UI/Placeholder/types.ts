import type { ReactNode, SVGAttributes } from 'react';

export type TPlaceholderMood = 'good' | 'neutral' | 'bad';

export interface IPlaceholderIconProps extends SVGAttributes<SVGElement> {
  mood: TPlaceholderMood;
}

export interface IPlaceholderProps {
  mood?: TPlaceholderMood;
  Icon(props: IPlaceholderIconProps): JSX.Element;
  title: string;
  description?: string;
  footer?: ReactNode;
  containerClassName?: string;
}
