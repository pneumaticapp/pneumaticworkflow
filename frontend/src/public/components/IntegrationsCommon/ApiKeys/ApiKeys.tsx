import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { copyToClipboard } from '../../../utils/helpers';
import { Button } from '../../UI/Buttons/Button';
import { NotificationManager } from '../../UI/Notifications';
import { loadApiKeys, createApiKey, deleteApiKey, clearNewlyCreatedKey } from '../../../redux/actions';
import { getApiKeys, getAreApiKeysLoading, getNewlyCreatedApiKey } from '../../../redux/selectors/integrations';

import { ApiKeyListItem } from './ApiKeyListItem';
import { CreateApiKeyModal, NewApiKeyModal, RevokeApiKeyModal } from './ApiKeyModals';

import styles from './ApiKeys.css';

export function ApiKeys() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const apiKeys = useSelector(getApiKeys);
  const isLoading = useSelector(getAreApiKeysLoading);
  const newlyCreatedKey = useSelector(getNewlyCreatedApiKey);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    dispatch(loadApiKeys());

    return () => {
      dispatch(clearNewlyCreatedKey());
    };
  }, [dispatch]);

  const handleCreate = useCallback(
    (name: string) => {
      dispatch(createApiKey({ name: name || undefined }));
      setShowCreateForm(false);
    },
    [dispatch],
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
  }, []);

  const handleCopyNewlyCreatedKey = useCallback(() => {
    if (newlyCreatedKey) {
      copyToClipboard(newlyCreatedKey);
      NotificationManager.success({ message: 'integrations.api-key-copied' });
    }
  }, [newlyCreatedKey]);

  return (
    <>
      <section className={styles['api-keys']} aria-labelledby="api-keys-title" data-testid="api-keys-section">
        <header className={styles['api-keys__header']}>
          <h2 id="api-keys-title" className={styles['api-keys__title']}>
            {formatMessage({ id: 'integrations.api-keys-title' })}
          </h2>
          <Button
            className={styles['api-keys__create-btn']}
            type="button"
            onClick={handleShowCreateForm}
            size="sm"
            buttonStyle="yellow"
            label={formatMessage({ id: 'integrations.create-api-key' })}
            data-testid="create-api-key-btn"
          />
        </header>

        {isLoading && (
          <p className={styles['api-keys__loading']}>{formatMessage({ id: 'integrations.loading-api-key' })}</p>
        )}

        {!isLoading && apiKeys.length === 0 && (
          <p className={styles['api-keys__empty']} data-testid="empty-keys-message">
            {formatMessage({ id: 'integrations.no-api-keys' })}
          </p>
        )}

        {!isLoading && apiKeys.length > 0 && (
          <ul className={styles['api-keys__list']} data-testid="api-keys-list">
            {apiKeys.map((key) => (
              <ApiKeyListItem key={key.id} apiKey={key} onRevoke={handleConfirmDeleteStart} />
            ))}
          </ul>
        )}
      </section>

      <NewApiKeyModal apiKey={newlyCreatedKey} onClose={handleCloseNewKeyModal} onCopy={handleCopyNewlyCreatedKey} />
      <RevokeApiKeyModal
        isOpen={confirmDeleteId !== null}
        onClose={handleConfirmDeleteCancel}
        onConfirm={handleDelete}
      />
      <CreateApiKeyModal isOpen={showCreateForm} onSubmit={handleCreate} onClose={handleHideCreateForm} />
    </>
  );
}
