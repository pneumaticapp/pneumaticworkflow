/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import Slider, { SliderProps, Handle, HandleProps } from 'rc-slider';

import 'rc-slider/assets/index.css';

import styles from './Slider.css';
import { SliderHandleArrowLeftIcon, SliderHandleArrowRightIcon } from '../icons';

export interface ISliderProps extends SliderProps { }

const SliderComponent = Slider as unknown as Function;

export function CustomSlider(props: ISliderProps) {
  return (
    <div className={styles['container']} >
      <SliderComponent
        handle={CustomHandle}
        {...props}
      />
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
