import React from 'react';
import { useIntl } from 'react-intl';

import { Modal } from '../../UI/Modal';
import { RichText } from '../../RichText';
import { Button } from '../../UI';

import styles from './HelpModal.css';



interface IHelpModalProps {
  isOpen: boolean;
  helpText: string;
  onClose: () => void;
}

export function HelpModal({ isOpen, onClose, helpText }: IHelpModalProps) {
  const { formatMessage } = useIntl();

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div>
        <h3 className={styles['help-modal__title']}>{formatMessage({ id: 'task.help-modal.title' })}</h3>

        <div className={styles['help-modal__content']}>
          <RichText text={helpText} />
        </div>

        <div className={styles['help-modal__buttons']}>
          <Button
            type="button"
            buttonStyle="yellow"
            size="md"
            onClick={onClose}
            label={formatMessage({ id: 'task.help-modal.cancel' })}
          />
        </div>
      </div>
    </Modal>
  );
}
