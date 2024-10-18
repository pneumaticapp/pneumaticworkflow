import React, { ComponentProps } from 'react';
import Tippy from '@tippyjs/react';
import classnames from 'classnames';

import styles from './Tooltip.css';

type TTooltipSize = 'md' | 'lg' | 'auto';

interface ITooltipProps extends ComponentProps<typeof Tippy> {
  isDarkBackground?: boolean;
  size?: TTooltipSize;
  containerClassName?: string;
  contentClassName?: string;
}

const SMALL_ARROW_SVG_STRING = `<svg width="12" height="4" xmlns="http://www.w3.org/2000/svg" fill="none">
  <path fill="#62625F" d="M.055 4h6V0c0 2.21-2.686 4-6 4z"/>
  <path fill="#62625F" d="M12.046 3.993h-6v-4c0 2.21 2.686 4 6 4z"/>
  </svg>`;

const LARGE_ARROW_SVG_STRING = `<svg width="24" height="8" viewBox="0 0 24 8" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M1.43051e-06 8.00006L12 8.00006L12 6.10352e-05C12 4.41834 6.62741 8.00006 1.43051e-06 8.00006Z" fill="#40403D"/>
  <path d="M24 8.00006L12 8.00006L12 6.10352e-05C12 4.41834 17.3726 8.00006 24 8.00006Z" fill="#40403D"/>
  </svg>`;

export const Tooltip = ({
  size = 'md',
  isDarkBackground,
  content,
  containerClassName,
  contentClassName,
  ...props
}: ITooltipProps) => {
  const sizeMaxWidthMap = {
    md: 192,
    lg: 304,
    auto: 'auto',
  };

  const classNameMap = {
    md: styles['tooltip_md'],
    lg: styles['tooltip_lg'],
    auto: null,
  };

  const offsetMap: { [key in TTooltipSize]: [number, number] } = {
    md: [0, 4],
    lg: [0, 8],
    auto: [0, 0],
  };

  return (
    <div className={classnames(classNameMap[size], isDarkBackground && styles['tooltip_dark'], containerClassName)}>
      <Tippy
        interactive
        offset={offsetMap[size]}
        arrow={size === 'lg' ? LARGE_ARROW_SVG_STRING : SMALL_ARROW_SVG_STRING}
        maxWidth={sizeMaxWidthMap[size]}
        content={content && <div className={classnames(styles['content'], contentClassName)}>{content}</div>}
        {...props}
      >
        {props.children}
      </Tippy>
    </div>
  );
};
