import * as React from 'react';
import { useState } from 'react';
import classnames from 'classnames';
import { UncontrolledDropdown, DropdownToggle, DropdownMenu as ReactstrapDropdownMenu } from 'reactstrap';
import OutsideClickHandler from 'react-outside-click-handler';

import { ConfirmableDropdownItem } from './ConfirmableDropdownItem';
import type { IDropdownMenuPanelProps, IDropdownMenuProps, TDropdownItemColor, TDropdownMenuOption } from './types';
import { isArrayWithItems } from '../../../utils/helpers';
import { ArrowRightIcon } from '../../icons';

import styles from './DropdownMenu.css';
import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { Tooltip } from '../Tooltip';

export const getDropdownItemColorClass = (color: TDropdownItemColor = 'black') => {
  const colorClassMap = {
    black: styles['dropdown-item_black'],
    green: styles['dropdown-item_green'],
    red: styles['dropdown-item_red'],
    orange: styles['dropdown-item_orange'],
  };

  return colorClassMap[color];
};

export function DropdownMenu({
  options,
  direction,
  className,
  toggleProps,
  menuClassName,
  menuPositionFixed = false,
  menuContainer,
  renderToggle,
  renderMenuContent,
  CustomDropdownMenu,
  isFromBreakdownItem,
  isDisabled = false,
}: IDropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { isDesktop, isMobile } = useCheckDevice();
  const onToggle = () => {
    if (isDisabled) return;
    setIsOpen((prev) => !prev);
  };

  const closeDropdown = () => {
    setIsOpen(false);
  };

  const renderOptions = (items: TDropdownMenuOption[] | TDropdownMenuOption, level = 0): React.ReactNode => {
    const overlayAtRoot = level === 0;
    const positionFixed = Boolean(menuPositionFixed && overlayAtRoot);
    const container = overlayAtRoot ? menuContainer : undefined;

    if (!Array.isArray(items)) {
      const Menu = CustomDropdownMenu || DropdownMenuPanel;

      return (
        <Menu
          isWide
          renderedOptions={items.customSubOption}
          level={level}
          direction={direction}
          className={menuClassName}
          renderMenuContent={renderMenuContent}
          positionFixed={positionFixed}
          container={container}
        />
      );
    }

    const renderedOptions = items.map((option) => {
      const {
        label,
        mapKey,
        customSubOption,
        color,
        subOptions,
        withUpperline,
        withConfirmation,
        initialConfirmationState,
        isHidden,
        isDisabled: isOptionDisabled,
        disabledTooltip,
        className: optionClassName,
        Icon,
        onClick,
      } = option;

      if (isHidden) return null;

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

      if (customSubOption || (subOptions && Array.isArray(subOptions) && isArrayWithItems(subOptions))) {
        return (
          <UncontrolledDropdown
            key={`submenu-${typeof label === 'string' ? label : mapKey}`}
            direction="right"
            className={optionClassName}
          >
            <DropdownToggle
              tag="button"
              className={classnames(styles['dropdown-item'], getDropdownItemColorClass(color))}
            >
              <span className={styles['label']}>{label}</span>
              <ArrowRightIcon className={styles['dropdown-item-icon']} />
            </DropdownToggle>
            {subOptions ? (
              renderOptions(subOptions, level + 1)
            ) : (
              <DropdownMenuPanel
                className={styles['dropdown__custom-sub-options']}
                renderedOptions={customSubOption}
                isWide
                level={level + 1}
                positionFixed={false}
              />
            )}
          </UncontrolledDropdown>
        );
      }

      const optionContent = (
        <div key={`option-${typeof label === 'string' ? label : mapKey}`}>
          {withUpperline && <hr className={styles['line']} />}
          <ConfirmableDropdownItem
            {...(!isOptionDisabled &&
              onClick && {
                onClick: () => {
                  onClick?.(() => setIsOpen(false));
                  closeDropdown();
                },
              })}
            cssModule={{
              'dropdown-item': classnames(styles['dropdown-item'], getDropdownItemColorClass(color), {
                [styles['dropdown-item-mobile']]: isMobile && isFromBreakdownItem,
                [styles['dropdown-item_disabled']]: isOptionDisabled,
              }),
            }}
            withConfirmation={withConfirmation}
            initialConfirmationState={initialConfirmationState}
            closeDropdown={closeDropdown}
            toggle={false}
            className={optionClassName}
          >
            {renderOptionContent()}
          </ConfirmableDropdownItem>
        </div>
      );

      if (isOptionDisabled && disabledTooltip) {
        return (
          <Tooltip
            key={`disabled-${typeof label === 'string' ? label : mapKey}`}
            content={disabledTooltip}
            placement="top"
            interactive={false}
            contentClassName={styles['dropdown-item-tooltip']}
          >
            {optionContent}
          </Tooltip>
        );
      }

      return optionContent;
    });
    const isWide = items.every((item) => item.size === 'lg');
    const Menu = CustomDropdownMenu || DropdownMenuPanel;

    // Only pass renderMenuContent to the top-level menu to prevent submenus from inheriting the parent's custom header
    return (
      <Menu
        renderedOptions={renderedOptions}
        isWide={isWide}
        level={level}
        direction={direction}
        className={menuClassName}
        positionFixed={positionFixed}
        container={container}
        {...(level === 0 && { renderMenuContent })}
      />
    );
  };

  return (
    <OutsideClickHandler disabled={!isOpen} onOutsideClick={onToggle}>
      <UncontrolledDropdown
        isOpen={isOpen}
        direction="down"
        onClick={(event) => event.stopPropagation()}
        className={classnames(
          styles['container'],
          isFromBreakdownItem && isDesktop && styles['dropdown-toggle-centered-container'],
          className,
        )}
        toggle={onToggle}
      >
        <DropdownToggle
          tag="button"
          className={classnames(
            styles['dropdown-toggle'],
            isFromBreakdownItem && isDesktop && styles['dropdown-toggle-centered'],
          )}
          {...(isDisabled && { disabled: true })}
          {...toggleProps}
        >
          {renderToggle(isOpen)}
        </DropdownToggle>
        {renderOptions(options)}
      </UncontrolledDropdown>
    </OutsideClickHandler>
  );
}

export function DropdownMenuPanel({
  renderedOptions,
  isWide,
  level,
  direction = 'right',
  className,
  renderMenuContent,
  positionFixed = false,
  container,
}: IDropdownMenuPanelProps) {
  const content = renderMenuContent?.(renderedOptions) || renderedOptions;

  return (
    <ReactstrapDropdownMenu
      cssModule={{
        'dropdown-menu': classnames(
          styles['dropdown-menu'],
          isWide && styles['dropdown-menu_wide'],
          !positionFixed && styles['dropdown-menu_bootstrap-placement'],
        ),
        show: styles['dropdown-menu_show'],
      }}
      right={level === 0 && direction === 'right'}
      className={className}
      modifiers={{ preventOverflow: { boundariesElement: 'window' } }}
      positionFixed={positionFixed}
      container={container}
    >
      {content}
    </ReactstrapDropdownMenu>
  );
}
