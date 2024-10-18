/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';
import { Tooltip, TooltipProps } from 'reactstrap';

import styles from './CustomTooltip.css';
import { ELearnMoreLinks } from '../../../constants/defaultValues';

export const enum ETooltipPlacement {
  Bottom = 'bottom',
  Top = 'top',
}

type TTooltipSize = 'md' | 'lg';

export interface ICustomTooltip extends Omit<TooltipProps, 'target' | 'isOpen'> {
  id?: string;
  tooltipTitle?: string;
  tooltipText?: string;
  placement?: ETooltipPlacement;
  target: React.RefObject<HTMLElement>;
  isOpen?: boolean;
  tooltipClassName?: string;
  learnMoreLink?: ELearnMoreLinks;
  size?: TTooltipSize;
}

export const CustomTooltip = ({
  id,
  isOpen: isTooltipOpenProp,
  tooltipTitle,
  tooltipText,
  target,
  toggle,
  placement = ETooltipPlacement.Top,
  tooltipClassName,
  learnMoreLink,
  size = 'md',
}: ICustomTooltip) => {
  const { formatMessage } = useIntl();

  const { useEffect, useState } = React;
  const [isTooltipOpenState, setIsTooltipOpenState] = useState(false);
  const openTooltip = () => setIsTooltipOpenState(true);
  const hideTooltip = () => setIsTooltipOpenState(false);

  const sizeClassNameMap = {
    md: styles['tooltip_md'],
    lg: styles['tooltip_lg'],
  };

  useEffect(() => {
    if (target && target.current) {
      target.current.addEventListener('mouseover', openTooltip);
      target.current.addEventListener('mouseleave', hideTooltip);
    }

    return () => {
      if (target && target.current) {
        target.current.removeEventListener('mouseover', openTooltip);
        target.current.removeEventListener('mouseleave', hideTooltip);
      }
    };
  }, [target.current]);

  const arrowClassName = classnames(
    styles['custom-arrow'],
    placement === 'top' ? styles['custom-arrow_bottom'] : styles['custom-arrow_top'],
  );

  const { messages } = useIntl();
  const title = tooltipTitle && (messages[tooltipTitle] || tooltipTitle);
  const text = tooltipText && (messages[tooltipText] || tooltipText);

  const isTooltipOpen = typeof isTooltipOpenProp === 'boolean' ? isTooltipOpenProp : isTooltipOpenState;

  if (!target.current) {
    return null;
  }

  return (
    <Tooltip
      id={id}
      arrowClassName={arrowClassName}
      modifiers={{ preventOverflow: { boundariesElement: 'window' } }}
      autohide={false}
      className={classnames(tooltipClassName, styles['tooltip'], sizeClassNameMap[size])}
      delay={0}
      innerClassName={styles['inner']}
      isOpen={isTooltipOpen}
      placement={placement}
      target={target.current}
      toggle={toggle}
    >
      <p>
        {title && <span className={styles['title']}>{title}</span>}
        {text}
      </p>
      {learnMoreLink && (
        <p>
          <a href={learnMoreLink} target={'_blank'}>{formatMessage({id: 'general.learn-more'})}</a>
        </p>
      )}
    </Tooltip>
  );
};
