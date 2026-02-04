import React, { useState } from 'react';
import { useIntl } from 'react-intl';

import { Modal } from '../../UI/Modal';
import { RichEditor } from '../../RichEditor';
import { Button } from '../../UI';

import styles from './ReturnModal.css';

interface IReturnModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (message: string) => void;
}

export function ReturnModal({ isOpen, onClose, onConfirm }: IReturnModalProps) {
  const { formatMessage } = useIntl();
  const [returnMessage, setReturnMessage] = useState('');
  const isModal = true;

  const handleConfirm = () => {
    onConfirm(returnMessage);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div>
        <p className={styles['return-modal__title']}>{formatMessage({ id: 'task.return-to.title' })}</p>

        <p className={styles['return-modal__subtitle']}>{formatMessage({ id: 'task.return-to.subtitle' })}</p>

        <div className={styles['return-modal__editor']}>
          <RichEditor
            placeholder={formatMessage({ id: 'task.return-to.placeholder' })}
            handleChange={async (message) => {
              setReturnMessage(message);
              return message;
            }}
            isModal={isModal}
          />
        </div>

        <div className={styles['return-modal__buttons']}>
          <Button
            disabled={Boolean(!returnMessage)}
            type="button"
            buttonStyle="yellow"
            size="md"
            onClick={handleConfirm}
            label={formatMessage({ id: 'task.return-to.confirm' })}
          />
          <Button
            type="button"
            buttonStyle="link-dark-text"
            size="md"
            onClick={onClose}
            label={formatMessage({ id: 'task.return-to.cancel' })}
          />
        </div>
      </div>
    </Modal>
  );
}
