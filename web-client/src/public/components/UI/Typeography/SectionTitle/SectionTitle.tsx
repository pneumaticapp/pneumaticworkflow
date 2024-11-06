import * as React from 'react';
import * as classnames from 'classnames';

import styles from './SectionTitle.css';

interface ISectionTitleProps {
  className?: string;
  children: string | React.ReactNode;
}

export function SectionTitle({ className, children }: ISectionTitleProps) {
  return (
    <p className={classnames(styles['container'], className)}>
      {children}
    </p>
  );
}
