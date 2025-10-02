import React from 'react';
import { BaseModal, ModalBody, ModalFooter, ModalHeader } from '../BaseModal';
import { Button } from '..';

import styles from './WarningPopup.css';

export interface IWarningPopupProps {
  acceptTitle?: string;
  declineTitle?: string;
  message: string | React.JSX.Element | (string | React.JSX.Element)[];
  isOpen?: boolean;
  title: string;
  onConfirm(): void;
  onReject(): void;
  closeModal(): void;
  renderCustomControlls?(confirm: () => void, reject: () => void): React.ReactNode;
}

export function WarningPopup({
  acceptTitle,
  declineTitle,
  message,
  isOpen,
  title,
  onConfirm,
  onReject,
  closeModal,
  renderCustomControlls,
}: IWarningPopupProps) {
  const handleSubmitClick = () => {
    onConfirm();
    closeModal();
  };

  return (
    <BaseModal isOpen={isOpen || false} toggle={closeModal}>
      <ModalHeader toggle={closeModal}>{title}</ModalHeader>
      <ModalBody>{message}</ModalBody>
      <ModalFooter>
        <div className={styles['popup-buttons']}>
          {renderCustomControlls ? (
            renderCustomControlls(onConfirm, onReject)
          ) : (
            <>
              <Button
                className={styles['popup-button_submit']}
                onClick={handleSubmitClick}
                label={acceptTitle}
                buttonStyle="yellow"
                size="md"
              />
              <button type="button" className="cancel-button" onClick={onReject}>
                {declineTitle}
              </button>
            </>
          )}
        </div>
      </ModalFooter>
    </BaseModal>
  );
}
