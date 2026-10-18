import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { copyToClipboard } from '../../../utils/helpers';
import { Button } from '../../UI/Buttons/Button';
import { NotificationManager } from '../../UI/Notifications';
import { loadApiKeys, createApiKey, deleteApiKey, clearNewlyCreatedKey } from '../../../redux/actions';
import { getApiKeys, getAreApiKeysLoading, getNewlyCreatedApiKey } from '../../../redux/selectors/integrations';

import { ApiKeyListItem } from './ApiKeyListItem';
import { CreateApiKeyModal, NewApiKeyModal, RevokeApiKeyModal } from './ApiKeyModals';

import styles from '../IntegrationsCommon.css';

export function ApiKeys() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const apiKeys = useSelector(getApiKeys);
  const isLoading = useSelector(getAreApiKeysLoading);
  const newlyCreatedKey = useSelector(getNewlyCreatedApiKey);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    dispatch(loadApiKeys());

    return () => {
      dispatch(clearNewlyCreatedKey());
    };
  }, [dispatch]);

  const handleCreate = useCallback(() => {
    dispatch(createApiKey({ name: newKeyName || undefined }));
    setNewKeyName('');
    setShowCreateForm(false);
  }, [newKeyName, dispatch]);

  const handleCreateSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      handleCreate();
    },
    [handleCreate],
  );

  const handleDelete = useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteApiKey({ id: confirmDeleteId }));
      setConfirmDeleteId(null);
    }
  }, [confirmDeleteId, dispatch]);

  const handleConfirmDeleteStart = useCallback((id: number) => {
    setConfirmDeleteId(id);
  }, []);

  const handleConfirmDeleteCancel = useCallback(() => {
    setConfirmDeleteId(null);
  }, []);

  const handleCloseNewKeyModal = useCallback(() => {
    dispatch(clearNewlyCreatedKey());
  }, [dispatch]);

  const handleShowCreateForm = useCallback(() => {
    setShowCreateForm(true);
  }, []);

  const handleHideCreateForm = useCallback(() => {
    setShowCreateForm(false);
    setNewKeyName('');
  }, []);

  const handleCopyNewlyCreatedKey = useCallback(() => {
    if (newlyCreatedKey) {
      copyToClipboard(newlyCreatedKey);
      NotificationManager.success({ message: 'integrations.api-key-copied' });
    }
  }, [newlyCreatedKey]);

  const handleNameChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setNewKeyName(e.target.value);
  }, []);

  return (
    <>
      <div className={styles['api-keys']} data-testid="api-keys-section">
        <div className={styles['api-keys__header']}>
          <p className={styles['api-keys__title']}>{formatMessage({ id: 'integrations.api-keys-title' })}</p>
          <Button
            className={styles['api-keys__create-btn']}
            type="button"
            onClick={handleShowCreateForm}
            size="sm"
            buttonStyle="yellow"
            label={formatMessage({ id: 'integrations.create-api-key' })}
            data-testid="create-api-key-btn"
          />
        </div>

        {isLoading && (
          <p className={styles['api-keys__loading']}>{formatMessage({ id: 'integrations.loading-api-key' })}</p>
        )}

        {!isLoading && apiKeys.length === 0 && (
          <p className={styles['api-keys__empty']} data-testid="empty-keys-message">
            {formatMessage({ id: 'integrations.no-api-keys' })}
          </p>
        )}

        {!isLoading && apiKeys.length > 0 && (
          <div className={styles['api-keys__list']} data-testid="api-keys-list">
            {apiKeys.map((key) => (
              <ApiKeyListItem key={key.id} apiKey={key} onRevoke={handleConfirmDeleteStart} />
            ))}
          </div>
        )}
      </div>

      <NewApiKeyModal apiKey={newlyCreatedKey} onClose={handleCloseNewKeyModal} onCopy={handleCopyNewlyCreatedKey} />
      <RevokeApiKeyModal
        isOpen={confirmDeleteId !== null}
        onClose={handleConfirmDeleteCancel}
        onConfirm={handleDelete}
      />
      <CreateApiKeyModal
        isOpen={showCreateForm}
        name={newKeyName}
        onNameChange={handleNameChange}
        onSubmit={handleCreateSubmit}
        onClose={handleHideCreateForm}
      />
    </>
  );
}
