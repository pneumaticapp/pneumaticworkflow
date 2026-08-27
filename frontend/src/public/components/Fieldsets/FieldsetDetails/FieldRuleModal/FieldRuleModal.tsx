import * as React from 'react';
import { useIntl } from 'react-intl';

import { BaseModal, ModalHeader, ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { Button } from '../../../UI/Buttons/Button';
import { IFieldRuleSet } from '../../../../types/fieldset';
import { IFieldRuleModalProps } from './types';
import { createEmptyFieldRuleSet } from './utils';
import { FieldRulesetBody } from './FieldRulesetBody';

import styles from './FieldRuleModal.css';

export function FieldRuleModal({
  isOpen,
  ruleset,
  rulesFieldOptions,
  onSave,
  onClose,
}: IFieldRuleModalProps) {
  const { formatMessage } = useIntl();
  const [localRuleSet, setLocalRuleSet] = React.useState<IFieldRuleSet>(
    () => ruleset || createEmptyFieldRuleSet(),
  );

  React.useEffect(() => {
    if (isOpen) {
      setLocalRuleSet(ruleset || createEmptyFieldRuleSet());
    }
  }, [isOpen]);

  const updateRuleSet = (changes: Partial<IFieldRuleSet>) => {
    setLocalRuleSet((prev) => ({ ...prev, ...changes }));
  };

  return (
    <BaseModal isOpen={isOpen} toggle={onClose} className={styles['modal-dialog']}>
      <ModalHeader toggle={onClose}>
        {formatMessage({ id: 'fieldsets.field-rule-modal.title' })}
      </ModalHeader>
      <ModalBody>
        <FieldRulesetBody
          localRuleSet={localRuleSet}
          rulesFieldOptions={rulesFieldOptions}
          onUpdateRuleSet={updateRuleSet}
        />
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
            buttonStyle="yellow"
            label={formatMessage({ id: 'fieldsets.field-rule-modal.save' })}
            onClick={() => onSave(localRuleSet)}
            size="md"
          />
        </div>
      </ModalFooter>
    </BaseModal>
  );
}
