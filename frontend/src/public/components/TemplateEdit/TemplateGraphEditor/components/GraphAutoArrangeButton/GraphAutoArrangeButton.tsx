import * as React from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../../../../UI';
import styles from './GraphAutoArrangeButton.css';

export interface IGraphAutoArrangeButtonProps {
  /** Enabled only when the user has moved at least one card away from the automatic layout. */
  isActive: boolean;
  onReset: () => void;
}

export const GraphAutoArrangeButton = ({ isActive, onReset }: IGraphAutoArrangeButtonProps) => {
  const { formatMessage } = useIntl();

  return (
    <Button
      className={styles['graph-auto-arrange']}
      type="button"
      buttonStyle="yellow"
      size="sm"
      label={formatMessage({ id: 'template.graph-auto-arrange' })}
      disabled={!isActive}
      onClick={onReset}
      data-test-id="graph-auto-arrange"
    />
  );
};
