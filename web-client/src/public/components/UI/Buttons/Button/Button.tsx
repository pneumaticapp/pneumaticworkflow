import * as React from 'react';
import classnames from 'classnames';
import { Link, NavLinkProps } from 'react-router-dom';
import { Loader, TSpinnerColor } from '../../Loader';

import styles from './Button.css';

export const Button = React.forwardRef(
  (
    {
      className,
      labelClassName,
      buttonStyle = 'black',
      disabled,
      label,
      isLoading,
      onClick,
      size = 'lg',
      type,
      icon: Icon,
      wrapper = 'button',
      to = '',
      // tslint:disable-next-line: trailing-comma
      ...rest
    }: TButtonProps,
    ref,
  ) => {
    const Wrapper = wrapper;
    const buttonSizeClass = styles[buttonSizeClassMap[size]];
    const buttonStyleClass = styles[buttonStyleClassMap[buttonStyle]];

    return (
      <Wrapper
        // @ts-ignore
        ref={ref}
        className={classnames(
          styles['button'],
          buttonSizeClass,
          buttonStyleClass,
          !label && styles['button_no-label'],
          Icon && styles['button_with-icon'],
          isLoading && styles['button_is-loading'],
          className,
        )}
        onClick={onClick}
        disabled={disabled || isLoading}
        type={type}
        to={to}
        {...rest}
      >
        <Loader isLoading={isLoading} spinnerColor={loaderColorMap[buttonStyle]} />
        {Icon && <Icon className={classnames(styles['icon'], isLoading && styles['button-inner_hidden'])} />}
        {label && (
          <span className={classnames(isLoading && styles['button-inner_hidden'], labelClassName)}>{label}</span>
        )}
      </Wrapper>
    );
  },
);

type TButtonStyle = 'yellow' | 'black' | 'transparent-yellow' | 'transparent-orange' | 'transparent-black';

type TButtonConditionalProps =
  | {
      wrapper?: 'a';
      href?: string;
      target?: string;
      to?: never;
      type?: never;
    }
  | {
      wrapper?: 'button';
      type?: React.ComponentProps<'button'>['type'];
      target?: never;
      to?: never;
    }
  | {
      wrapper?: typeof Link;
      to: NavLinkProps['to'];
      targer?: never;
      type?: never;
    };

type TButtonSize = 'sm' | 'md' | 'lg';

export interface IButtonCommonProps {
  className?: string;
  labelClassName?: string;
  buttonStyle?: TButtonStyle;
  label?: string;
  isLoading?: boolean;
  size?: TButtonSize;
  icon?(props: React.SVGAttributes<SVGElement>): JSX.Element;
  onClick?(e: React.MouseEvent): void;
  disabled?: boolean;
}

const buttonSizeClassMap: { [key in TButtonSize]: string } = {
  sm: 'button_sm',
  md: 'button_md',
  lg: 'button_lg',
};

const buttonStyleClassMap: { [key in TButtonStyle]: string } = {
  yellow: 'button_yellow',
  black: 'button_black',
  'transparent-yellow': 'button_transparent-yellow',
  'transparent-orange': 'button_transparent-orange',
  'transparent-black': 'button_transparent-black',
};

const loaderColorMap: { [key in TButtonStyle]: TSpinnerColor } = {
  yellow: 'white',
  black: 'yellow',
  'transparent-yellow': 'yellow',
  'transparent-orange': 'yellow',
  'transparent-black': 'yellow',
};

export type TButtonProps = IButtonCommonProps & TButtonConditionalProps;
