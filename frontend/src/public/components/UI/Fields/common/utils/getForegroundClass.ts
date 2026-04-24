import { TForegroundColor } from '../types';

import commonStyles from '../styles.css';



export function getForegroundClass(foreground: TForegroundColor) {
  const foregroundClassMap: { [key in TForegroundColor]: string } = {
    white: commonStyles['title_foreground-white'],
    beige: commonStyles['title_foreground-beige'],
  };

  return foregroundClassMap[foreground];
}
