import commonStyles from '../styles.css';
import { TForegroundColor } from '../types';

export function getForegroundClass(foreground: TForegroundColor) {
  const foregroundClassMap: { [key in TForegroundColor]: string } = {
    white: commonStyles['title_foreground-white'],
    beige: commonStyles['title_foreground-beige'],
  };

  return foregroundClassMap[foreground];
}
