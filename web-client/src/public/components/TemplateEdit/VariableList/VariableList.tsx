import React, { MouseEventHandler, useRef, useState } from 'react';
import OutsideClickHandler from 'react-outside-click-handler';
import * as PerfectScrollbar from 'react-perfect-scrollbar';
import { Tooltip as ReactstrapTooltip } from 'reactstrap';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { Tooltip, CustomTooltip } from '../../UI';
import { isArrayWithItems } from '../../../utils/helpers';
import { ExpandIcon } from '../../icons';
import { ELearnMoreLinks } from '../../../constants/defaultValues';
import { TTaskVariable } from '../types';
import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { TooltipRichContent } from '../TooltipRichContent';
import styles from './VariableList.css';

export interface IVariableListProps {
  variables: TTaskVariable[];
  className?: string;
  tooltipText: string;
  onVariableClick(apiName: string): (e: React.MouseEvent) => void;
  focusEditor(): void;
}

const ScrollBar = PerfectScrollbar as unknown as Function;

export const VariableList = ({
  variables,
  className,
  tooltipText,
  onVariableClick,
  focusEditor,
}: IVariableListProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isTooltipOpen, setIsTooltipOpen] = useState(false);
  const { isDesktop } = useCheckDevice();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const { formatMessage } = useIntl();
  const handleOutsideClick = () => {
    if (isOpen) {
      setIsOpen(false);
    }
  };

  const handleButtonClick: MouseEventHandler<HTMLButtonElement> = () => {
    if (!isArrayWithItems(variables)) {
      return;
    }

    setIsOpen(!isOpen);
    focusEditor();
  };

  return (
    <div className={className}>
      <button
        type="button"
        ref={buttonRef}
        className={classnames(styles['button'], isOpen && styles['button_opened'])}
        onClick={handleButtonClick}
        onMouseOver={() => setIsTooltipOpen(true)}
        onMouseLeave={() => setIsTooltipOpen(false)}
        onFocus={() => setIsTooltipOpen(true)}
        onBlur={() => setIsTooltipOpen(false)}
      >
        <span>{formatMessage({ id: 'template.insert-variable' })}</span>
        <ExpandIcon className={styles['button__expand-icon']} />

        <CustomTooltip
          isOpen={isTooltipOpen}
          target={buttonRef}
          tooltipText={tooltipText}
          learnMoreLink={ELearnMoreLinks.HowToCreateTemplate}
        />
      </button>

      <ReactstrapTooltip
        fade
        flip
        hideArrow
        innerClassName={styles['variable-list__inner']}
        className={styles['variable-list']}
        isOpen={isOpen}
        target={buttonRef.current!}
        {...(isDesktop && { placement: 'bottom-end' })}
      >
        <OutsideClickHandler onOutsideClick={handleOutsideClick}>
          <ScrollBar
            className={styles['variable-list__scrollbar']}
            options={{ suppressScrollX: true, wheelPropagation: false }}
          >
            {variables.map(({ title, richSubtitle, subtitle, apiName }) => {
              return (
                <Tooltip
                  interactive={false}
                  containerClassName={styles['condition__tooltop']}
                  content={<TooltipRichContent title={title} subtitle={subtitle} variables={variables} />}
                >
                  <p
                    className={styles['variable-list-item']}
                    onClick={onVariableClick(apiName)}
                    key={apiName}
                    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-to-interactive-role
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && onVariableClick(apiName)}
                  >
                    <span className={styles['variable-list-item__name']}>{title}</span>
                    <span className={styles['variable-list-item__task-name']}>{richSubtitle || subtitle}</span>
                  </p>
                </Tooltip>
              );
            })}
          </ScrollBar>
        </OutsideClickHandler>
      </ReactstrapTooltip>
    </div>
  );
};
