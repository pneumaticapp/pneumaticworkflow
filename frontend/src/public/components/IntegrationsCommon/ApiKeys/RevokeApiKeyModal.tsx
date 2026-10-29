import React from 'react';
import { useIntl } from 'react-intl';

import { WarningPopup } from '../../UI/WarningPopup';
import type { IRevokeApiKeyModalProps } from './types';

export function RevokeApiKeyModal({ isOpen, onClose, onConfirm }: IRevokeApiKeyModalProps) {
  const { formatMessage } = useIntl();

  return (
    <WarningPopup
      isOpen={isOpen}
      title={formatMessage({ id: 'integrations.revoke-modal-title' })}
      message={formatMessage({ id: 'integrations.delete-api-key-confirm' })}
      acceptTitle={formatMessage({ id: 'integrations.api-key-revoke' })}
      declineTitle={formatMessage({ id: 'integrations.cancel' })}
      onConfirm={onConfirm}
      onReject={onClose}
      closeModal={onClose}
    />
  );
}
