/* eslint-disable */
/* prettier-ignore */
import * as classnames from 'classnames';
import * as React from 'react';
import { useIntl } from 'react-intl';

import { scrollToElement } from '../../../utils/helpers';
import {
  DELAY_TITLE_TEMPLATE,
  formatDuration,
} from '../../../utils/dateTime';
import { IntlMessages } from '../../IntlMessages';
import { EditIcon, MoreIcon, TrashIcon } from '../../icons';
import { Duration } from '../../UI/Duration';
import { EMPTY_DURATION } from '../constants';
import { Dropdown, TDropdownOption } from '../../UI';

import styles from './Delay.css';

export interface IDelayProps {
  taskDelay: string | null;
  isDelayOpen?: boolean;
  deleteDelay(): void;
  editDelay(delay: string): void;
  toggleDelay(): void;
}

export function Delay({
  taskDelay,
  isDelayOpen,
  deleteDelay,
  editDelay,
  toggleDelay,
}: IDelayProps) {
  if (!taskDelay) {
    return null;
  }

  const { useEffect, useState } = React;
  const { formatMessage } = useIntl();

  const wrapperRef = React.useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(Boolean(isDelayOpen));

  useEffect(() => {
    if (wrapperRef.current && isDelayOpen) {
      scrollToElement(wrapperRef.current);
    }
  }, []);

  useEffect(() => {
    const isJustOpened = isDelayOpen && !open;

    if (wrapperRef.current && isJustOpened) {
      scrollToElement(wrapperRef.current);
    }

    setOpen(Boolean(isDelayOpen));
  }, [isDelayOpen]);

  const getDelayTitle = () => {
    const isFullDelayShown = taskDelay !== EMPTY_DURATION && !isDelayOpen;

    if (isFullDelayShown) {
      const delayFor = formatMessage({ id: 'template.delay-for' });
      const duration = formatDuration(taskDelay, DELAY_TITLE_TEMPLATE);

      return `${delayFor} ${duration}`;
    }

    return formatMessage({ id: 'template.delay' });
  };

  const handleOptionClick = (handler: () => void) =>  (closeDropdown: () => void) => {
    closeDropdown();
    handler();
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'template.delay-edit' }),
      onClick: handleOptionClick(toggleDelay),
      Icon: EditIcon,
      size: "sm",
      isHidden: isDelayOpen,
    },
    {
      label: formatMessage({ id: 'template.delay-close' }),
      onClick: handleOptionClick(toggleDelay),
      size: "sm",
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
    }
  ];

  return (
    <div ref={wrapperRef} className={styles['delay']}>
      <span className={styles['header__title']} onClick={toggleDelay}>
        {getDelayTitle()}
      </span>

      <div className={styles['card-more-container']}>
        <Dropdown
          renderToggle={isOpen => (
            <MoreIcon
              className={classnames(styles['card-more'], isOpen && styles['card-more_active'])}
            />
          )}
          options={dropdownOptions}
        />
      </div>

      {isDelayOpen &&
        <>
          <div className={styles['delay__body']}>
            <p className={styles['body__hint']}>
              <IntlMessages id="template.delay-hint" />
            </p>
            <Duration duration={taskDelay} onEditDuration={editDelay} />
          </div>
        </>
      }
    </div>
  );
}
