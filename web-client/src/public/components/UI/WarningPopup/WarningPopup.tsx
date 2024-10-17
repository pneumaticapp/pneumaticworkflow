import React from 'react';
import classnames from 'classnames';
import { Modal, ModalBody, ModalFooter, ModalHeader } from 'reactstrap';
import { Button } from "..";

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
    <Modal centered isOpen={isOpen} wrapClassName={classnames('team-popup')} toggle={closeModal}>
      <ModalHeader toggle={closeModal} className={styles['header']}>
        <p className={styles['title']}>{title}</p>
      </ModalHeader>
      <ModalBody className={styles['body']}>{message}</ModalBody>
      <ModalFooter className={styles['footer']}>
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
    </Modal>
  );
}
