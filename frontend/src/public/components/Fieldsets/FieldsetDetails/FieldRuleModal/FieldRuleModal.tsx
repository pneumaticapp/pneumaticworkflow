import * as React from 'react';
import { useIntl } from 'react-intl';

import { BaseModal, ModalHeader, ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { Button } from '../../../UI/Buttons/Button';
import { IFieldRuleModalProps } from './types';

import styles from './FieldRuleModal.css';

export function FieldRuleModal({
  isOpen,
  onClose,
  onSave,
  onDelete,
}: IFieldRuleModalProps) {
  const { formatMessage } = useIntl();

  return (
    <BaseModal isOpen={isOpen} toggle={onClose}>
      <ModalHeader toggle={onClose}>
        {formatMessage({ id: 'fieldsets.field-rule-modal.title' })}
      </ModalHeader>
      <ModalBody>
        {/* Rules content will be added in subsequent steps */}
      </ModalBody>
      <ModalFooter>
        <div className={styles['footer-buttons']}>
          <Button
            buttonStyle="transparent-black"
            label={formatMessage({ id: 'fieldsets.field-rule-modal.discard' })}
            onClick={onClose}
            size="md"
          />
          <Button
            buttonStyle="transparent-orange"
            label={formatMessage({ id: 'fieldsets.field-rule-modal.delete-rules' })}
            onClick={onDelete}
            size="md"
          />
          <Button
            buttonStyle="yellow"
            label={formatMessage({ id: 'fieldsets.field-rule-modal.save' })}
            onClick={onSave}
            size="md"
          />
        </div>
      </ModalFooter>
    </BaseModal>
  );
}
