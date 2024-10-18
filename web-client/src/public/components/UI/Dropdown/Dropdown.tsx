import React, { useState } from 'react';
import classnames from 'classnames';
import { UncontrolledDropdown, DropdownToggle, DropdownMenu } from 'reactstrap';
import OutsideClickHandler from 'react-outside-click-handler';

import { ConfirmableDropdownItem, TDropdownItemState } from './ConfirmableDropdownItem';

import { isArrayWithItems } from '../../../utils/helpers';
import { ArrowRightIcon } from '../../icons';

import styles from './Dropdown.css';

type TDropdownItemColor = 'black' | 'green' | 'red' | 'orange';

export type TDropdownOption = {
  label: React.ReactNode;
  withConfirmation?: boolean;
  initialConfirmationState?: TDropdownItemState;
  withUpperline?: boolean;
  subOptions?: TDropdownOption[];
  color?: TDropdownItemColor;
  isHidden?: boolean;
  size?: 'lg' | 'sm';
  className?: string;
  Icon?(props: React.SVGAttributes<SVGElement>): JSX.Element;
  onClick?(closeDropdown: () => void): void;
};

export interface IDropdownProps {
  options: TDropdownOption[];
  direction?: 'right' | 'left';
  className?: string;
  toggleProps?: { [key in string]: string };
  menuClassName?: string;
  renderToggle(isOpen: boolean): React.ReactNode;
  renderMenuContent?(renderedOptions: React.ReactNode): React.ReactNode;
  CustomDropdownMenu?(props: IDropdownMenuProps): JSX.Element;
}

export const getDropdownItemColorClass = (color: TDropdownItemColor = 'black') => {
  const colorClassMap = {
    black: styles['dropdown-item_black'],
    green: styles['dropdown-item_green'],
    red: styles['dropdown-item_red'],
    orange: styles['dropdown-item_orange'],
  };

  return colorClassMap[color];
};

export function Dropdown({
  options,
  direction,
  className,
  toggleProps,
  menuClassName,
  renderToggle,
  renderMenuContent,
  CustomDropdownMenu,
}: IDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);

  const onToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const renderOptions = (items: TDropdownOption[], level = 0): React.ReactNode => {
    const renderedOptions = items.map((option) => {
      const {
        label,
        color,
        subOptions,
        withUpperline,
        withConfirmation,
        initialConfirmationState,
        isHidden,
        className: optionClassName,
        Icon,
        onClick,
      } = option;

      if (isHidden) {
        return null;
      }

      const renderOptionContent = () => {
        if (typeof label === 'string') {
          return (
            <>
              <span className={styles['label']}>{label}</span>

              {Icon && <Icon className={styles['dropdown-item-icon']} />}
            </>
          );
        }

        return label;
      };

      if (!isArrayWithItems(subOptions)) {
        return (
          <div key={label?.toString()}>
            {withUpperline && <hr className={styles['line']} />}
            <ConfirmableDropdownItem
              {...(onClick && { onClick: () => onClick?.(() => setIsOpen(false)) })}
              cssModule={{
                'dropdown-item': classnames(styles['dropdown-item'], getDropdownItemColorClass(color)),
              }}
              withConfirmation={withConfirmation}
              initialConfirmationState={initialConfirmationState}
              closeDropdown={() => setIsOpen(false)}
              toggle={false}
              className={optionClassName}
            >
              {renderOptionContent()}
            </ConfirmableDropdownItem>
          </div>
        );
      }

      return (
        <UncontrolledDropdown direction="right">
          <DropdownToggle tag="button" className={styles['dropdown-item']}>
            <span className={styles['label']}>{label}</span>
            <ArrowRightIcon className={styles['dropdown-item-icon']} />
          </DropdownToggle>

          {renderOptions(subOptions, level + 1)}
        </UncontrolledDropdown>
      );
    });

    const isWide = items.every((item) => item.size === 'lg');

    const Menu = CustomDropdownMenu || DefaultDropdownMenu;

    return (
      <Menu
        renderedOptions={renderedOptions}
        isWide={isWide}
        level={level}
        direction={direction}
        className={menuClassName}
        renderMenuContent={renderMenuContent}
      />
    );
  };

  return (
    <OutsideClickHandler disabled={!isOpen} onOutsideClick={onToggle}>
      <UncontrolledDropdown
        isOpen={isOpen}
        direction="down"
        onClick={(event) => event.stopPropagation()}
        className={classnames(styles['container'], className)}
        toggle={onToggle}
      >
        <DropdownToggle tag="button" className={styles['dropdown-toggle']} {...toggleProps}>
          {renderToggle(isOpen)}
        </DropdownToggle>

        {renderOptions(options)}
      </UncontrolledDropdown>
    </OutsideClickHandler>
  );
}

export interface IDropdownMenuProps {
  renderedOptions: React.ReactNode;
  isWide: boolean;
  level: number;
  direction?: 'right' | 'left';
  className?: string;
  renderMenuContent?(renderedOptions: React.ReactNode): React.ReactNode;
}

export function DefaultDropdownMenu({
  renderedOptions,
  isWide,
  level,
  direction = 'right',
  className,
  renderMenuContent,
}: IDropdownMenuProps) {
  const content = renderMenuContent?.(renderedOptions) || renderedOptions;

  return (
    <DropdownMenu
      cssModule={{
        'dropdown-menu': classnames(styles['dropdown-menu'], isWide && styles['dropdown-menu_wide']),
        show: styles['dropdown-menu_show'],
      }}
      right={level === 0 && direction === 'right'}
      className={className}
      modifiers={{ preventOverflow: { boundariesElement: 'window' } }}
    >
      {content}
    </DropdownMenu>
  );
}
