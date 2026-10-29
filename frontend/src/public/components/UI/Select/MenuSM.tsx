import React from 'react';
import classnames from 'classnames';
import { components } from 'react-select';

export function MenuSM({ children, ...props }: any) {
  const customClassName = props.selectProps.classNames?.menuList?.(props);

  return (
    <div
      className={classnames(
        'react-select__menu-list',
        props.selectProps.isStaticMenu ? 'is-static' : 'is-sm',
        props.selectProps.isMulti && 'is-multi',
        props.selectProps.placement === 'left' && 'is-left',
        customClassName,
      )}
    >
      <components.Menu {...props}>{children}</components.Menu>
    </div>
  );
}
