import * as React from 'react';
import { ReactNode, useState, useEffect } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ExpandIcon } from '../../icons';
import styles from './ShowMore.css';

export type TShowMoreCommonProps = {
  containerClassName?: string;
  contentClassName?: string;
  toggleClassName?: string;
  activeLabelClassName?: string;
  arrowClassName?: string;
  label: string;
  innerRef?: React.RefObject<HTMLDivElement>;
  renderCustomLabel?(labelText: string): ReactNode;
  widget?: (toggle: () => void) => ReactNode;
};

type TControlledProps =
  | { toggle?(): never; isVisible?: never; isInitiallyVisible?: boolean }
  | { toggle(): void; isVisible: boolean; isInitiallyVisible?: never };

type TShowMoreProps = React.PropsWithChildren<
  TShowMoreCommonProps &
    TControlledProps & {
      isDisabled?: boolean;
    }
>;

export function ShowMore({
  isInitiallyVisible,
  containerClassName,
  contentClassName,
  label,
  toggleClassName,
  activeLabelClassName,
  arrowClassName,
  children,
  toggle,
  innerRef,
  isVisible: isVisibleProp,
  renderCustomLabel,
  widget,
  isDisabled,
}: TShowMoreProps) {
  const [isVisibleState, setVisibleState] = useState(Boolean(isInitiallyVisible));
  const { messages } = useIntl();

  useEffect(() => {
    if (isInitiallyVisible) {
      setVisibleState(isInitiallyVisible);
    }
  }, [isInitiallyVisible]);

  const toggleVisible = () => {
    if (toggle) {
      toggle();

      return;
    }

    setVisibleState(!isVisibleState);
  };

  const isVisible = typeof isVisibleProp === 'boolean' ? isVisibleProp : isVisibleState;

  const activeClassname = { ...(activeLabelClassName && { [activeLabelClassName]: isVisible }) };

  const renderToggleText = () => {
    const labelText = (messages[label] || label) as string;

    if (!renderCustomLabel) {
      return (
        <span className={classnames(styles['show_more__toggle-text'], isDisabled && styles['show_more--disabled'])}>
          {labelText}
        </span>
      );
    }

    return renderCustomLabel(labelText);
  };

  return (
    <div className={classnames(containerClassName, isVisible && styles['container--visible'])} ref={innerRef}>
      <div className={styles['show_more__button-wrapper']}>
        <button
          {...(isDisabled && { disabled: true })}
          type="button"
          onClick={toggleVisible}
          className={classnames(
            styles['show_more'],
            toggleClassName,
            activeClassname,
            isDisabled && styles['show_more--disabled'],
          )}
        >
          {renderToggleText()}

          <div className={classnames(arrowClassName, styles['show_more-icon-wrapper'])}>
            <ExpandIcon className={styles['show_more-icon']} />
          </div>
        </button>
        {widget && !isVisible && <div className={styles['show_more__right-vidgets']}>{widget(toggleVisible)}</div>}
      </div>
      {isVisible && <div className={classnames(styles['content'], contentClassName)}>{children}</div>}
    </div>
  );
}
