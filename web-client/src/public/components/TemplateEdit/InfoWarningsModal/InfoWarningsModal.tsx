import * as React from 'react';
import { useIntl } from 'react-intl';

import { IInfoWarningProps } from './warnings';

import { Header, Modal, Button } from '../../UI';

import styles from './InfoWarningsModal.css';

interface IInfoWarningsModalProps {
  isOpen: boolean;
  warnings: ((props: IInfoWarningProps) => JSX.Element)[];
  onClose(): void;
}

export function InfoWarningsModal({ isOpen, warnings, onClose }: IInfoWarningsModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
    >
      <Header tag="p" size="6">
        {formatMessage({ id: 'template.cannot-enable' })}
      </Header>

      <hr className={styles['line']} />

      {warnings.map(Warning => (
        <>
          <Warning onClickActionButton={onClose} />
          <hr className={styles['line']} />
        </>
      ))}

      <Button
        label={formatMessage({ id: 'template.waning-close-button' })}
        onClick={onClose}
        buttonStyle="yellow"
        size="md"
        className={styles['button']}
      />
    </Modal>
  );
}
