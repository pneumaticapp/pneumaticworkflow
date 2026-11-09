/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import Slider, { SliderProps, Handle, HandleProps } from 'rc-slider';
import { useIntl } from 'react-intl';
import { isRtlLocale } from '../../lang/direction';

import 'rc-slider/assets/index.css';

import styles from './Slider.css';
import { SliderHandleArrowLeftIcon, SliderHandleArrowRightIcon } from '../icons';

export interface ISliderProps extends SliderProps {}

const SliderComponent = Slider as unknown as Function;

export function CustomSlider(props: ISliderProps) {
  const { locale } = useIntl();
  return (
    <div className={styles['container']}>
      <SliderComponent handle={CustomHandle} reverse={isRtlLocale(locale)} {...props} />
    </div>
  );
}

const CustomHandle = (props: HandleProps) => {
  return (
    <Handle {...props}>
      <SliderHandleArrowLeftIcon />
      <SliderHandleArrowRightIcon />
    </Handle>
  );
};
