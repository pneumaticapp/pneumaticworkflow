export type TPlaceholderMood = 'good' | 'neutral' | 'bad';

export interface IPlaceholderIconProps extends React.SVGAttributes<SVGElement> {
  mood: TPlaceholderMood;
}
