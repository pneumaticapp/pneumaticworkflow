/* eslint-disable */
/* prettier-ignore */
import * as classnames from 'classnames';
import * as React from 'react';

import styles from './Header.css';

export type THeaderSize = 'xl' | '1' | '2' | '3' | '4' | '5' | '6';
interface IHeaderProps {
  tag: 'p' | 'span' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'button';
  size: THeaderSize;
  className?: string;
  children: React.ReactNode;
  withUnderline?: boolean;
  // tslint:disable-next-line: no-any
  [key: string]: any;
}

export function Header({ tag: Tag, size, className, children, withUnderline, ...rest }: IHeaderProps) {
  const sizeClassNameMap: { [key in THeaderSize]: string } = {
    xl: styles['size-xl'],
    1: styles['size-1'],
    2: styles['size-2'],
    3: styles['size-3'],
    4: styles['size-4'],
    5: styles['size-5'],
    6: styles['size-6'],
  };

  return (
    <Tag
      className={classnames(
        styles['common'],
        sizeClassNameMap[size],
        withUnderline && styles['with-underline'],
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}
