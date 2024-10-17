/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import OutsideClickHandler from 'react-outside-click-handler';
import * as PerfectScrollbar from 'react-perfect-scrollbar';
import { Tooltip } from 'reactstrap';
import * as classnames from 'classnames';
import { useIntl } from 'react-intl';

import styles from './VariableList.css';
import { isArrayWithItems } from '../../../utils/helpers';
import { ExpandIcon } from '../../icons';
import { ELearnMoreLinks } from '../../../constants/defaultValues';
import { CustomTooltip } from '../../UI';
import { TTaskVariable } from '../types';

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
  const [isOpen, setIsOpen] = React.useState(false);
  const [isTooltipOpen, setIsTooltipOpen] = React.useState(false);
  const buttonRef = React.useRef<HTMLButtonElement>(null);
  const { formatMessage } = useIntl();
  const handleOutsideClick = () => {
    if (isOpen) {
      setIsOpen(false);
    }
  };

  const handleButtonClick: React.MouseEventHandler<HTMLButtonElement> = (event) => {
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

      <Tooltip
        fade
        flip={true}
        hideArrow
        innerClassName={styles['variable-list__inner']}
        className={styles['variable-list']}
        isOpen={isOpen}
        placement="bottom-end"
        target={buttonRef.current!}
      >
        <OutsideClickHandler onOutsideClick={handleOutsideClick}>
          <ScrollBar
            className={styles['variable-list__scrollbar']}
            options={{ suppressScrollX: true, wheelPropagation: false }}
          >
            {variables.map(({ title, richSubtitle, subtitle, apiName }, index) => {
              return (
                <p className={styles['variable-list-item']} onClick={onVariableClick(apiName)} key={index}>
                  <span className={styles['variable-list-item__name']}>{title}</span>
                  <span className={styles['variable-list-item__task-name']}>{richSubtitle || subtitle}</span>
                </p>
              );
            })}
          </ScrollBar>
        </OutsideClickHandler>
      </Tooltip>
    </div>
  );
};
