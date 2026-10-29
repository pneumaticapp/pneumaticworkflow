import classnames from 'classnames';
import * as React from 'react';
import { useEffect, useRef } from 'react';
import { useIntl } from 'react-intl';

import { scrollToElement } from '../../../utils/helpers';
import { DELAY_TITLE_TEMPLATE, formatDuration } from '../../../utils/dateTime';
import { IntlMessages } from '../../IntlMessages';
import { EditIcon, MoreIcon, TrashIcon } from '../../icons';
import { Duration } from '../../UI/Duration';
import { START_DURATION } from '../constants';
import { DropdownMenu, TDropdownMenuOption } from '../../UI';

import styles from './Delay.css';

export interface IDelayProps {
  taskDelay: string | null;
  isDelayOpen?: boolean;
  deleteDelay(): void;
  editDelay(delay: string): void;
  toggleDelay(): void;
}

export function Delay({ taskDelay, isDelayOpen, deleteDelay, editDelay, toggleDelay }: IDelayProps) {
  const { formatMessage } = useIntl();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const wasDelayOpenRef = useRef(false);

  useEffect(() => {
    if (wrapperRef.current && isDelayOpen && !wasDelayOpenRef.current) {
      scrollToElement(wrapperRef.current);
    }

    wasDelayOpenRef.current = Boolean(isDelayOpen);
  }, [isDelayOpen]);

  if (!taskDelay) {
    return null;
  }

  const getDelayTitle = () => {
    const isFullDelayShown = taskDelay !== START_DURATION && !isDelayOpen;

    if (isFullDelayShown) {
      const delayFor = formatMessage({ id: 'template.delay-for' });
      const duration = formatDuration(taskDelay, DELAY_TITLE_TEMPLATE);

      return `${delayFor} ${duration}`;
    }

    return formatMessage({ id: 'template.delay' });
  };

  const handleTitleKeyDown = (event: React.KeyboardEvent<HTMLSpanElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    toggleDelay();
  };

  const handleOptionClick = (handler: () => void) => (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const dropdownOptions: TDropdownMenuOption[] = [
    {
      label: formatMessage({ id: 'template.delay-edit' }),
      onClick: handleOptionClick(toggleDelay),
      Icon: EditIcon,
      size: 'sm',
      isHidden: isDelayOpen,
    },
    {
      label: formatMessage({ id: 'template.delay-close' }),
      onClick: handleOptionClick(toggleDelay),
      size: 'sm',
      isHidden: !isDelayOpen,
    },
    {
      label: formatMessage({ id: 'template.delay-delete' }),
      onClick: deleteDelay,
      Icon: TrashIcon,
      color: 'red',
      size: 'sm',
      withConfirmation: true,
      withUpperline: true,
    },
  ];

  return (
    <div ref={wrapperRef} className={styles['delay']}>
      <span
        role="button"
        tabIndex={0}
        className={styles['header__title']}
        onClick={toggleDelay}
        onKeyDown={handleTitleKeyDown}
      >
        {getDelayTitle()}
      </span>

      <div className={styles['card-more-container']}>
        <DropdownMenu
          renderToggle={(isOpen) => (
            <MoreIcon className={classnames(styles['card-more'], isOpen && styles['card-more_active'])} />
          )}
          options={dropdownOptions}
        />
      </div>

      {isDelayOpen && (
        <>
          <div className={styles['delay__body']}>
            <p className={styles['body__hint']}>
              <IntlMessages id="template.delay-hint" />
            </p>
            <Duration duration={taskDelay} onEditDuration={editDelay} />
          </div>
        </>
      )}
    </div>
  );
}
