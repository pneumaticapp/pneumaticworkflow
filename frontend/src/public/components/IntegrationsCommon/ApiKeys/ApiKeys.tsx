import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { copyToClipboard } from '../../../utils/helpers';
import { Button } from '../../UI/Buttons/Button';
import { NotificationManager } from '../../UI/Notifications';
import { loadApiKeys, createApiKey, deleteApiKey, clearNewlyCreatedKey } from '../../../redux/actions';
import { getApiKeys, getApiKeysIsLoading, getApiKeysNewlyCreatedKey } from '../../../redux/selectors/integrations';

import { TokenListItemSkeleton } from '../TokenListItem';
import { ApiKeyListItem } from './ApiKeyListItem';
import { CreateApiKeyModal } from './CreateApiKeyModal';
import { NewApiKeyModal } from './NewApiKeyModal';
import { RevokeApiKeyModal } from './RevokeApiKeyModal';

import sectionStyles from '../IntegrationsCommon.css';
import tokenListStyles from '../TokenListItem/TokenListItem.css';

export function ApiKeys() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const apiKeys = useSelector(getApiKeys);
  const isLoading = useSelector(getApiKeysIsLoading);
  const newlyCreatedKey = useSelector(getApiKeysNewlyCreatedKey);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    dispatch(loadApiKeys());

    return () => {
      dispatch(clearNewlyCreatedKey());
    };
  }, [dispatch]);

  const handleCreate = useCallback(
    (name: string) => {
      dispatch(createApiKey({ name: name || undefined }));
      setIsCreateModalOpen(false);
    },
    [dispatch],
  );

  const handleDelete = useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteApiKey({ id: confirmDeleteId }));
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

  const handleOpenCreateModal = useCallback(() => {
    setIsCreateModalOpen(true);
  }, []);

  const handleCloseCreateModal = useCallback(() => {
    setIsCreateModalOpen(false);
  }, []);

  const handleCopyNewlyCreatedKey = useCallback(() => {
    if (newlyCreatedKey) {
      copyToClipboard(newlyCreatedKey);
      NotificationManager.success({ message: 'integrations.api-key-copied' });
    }
  }, [newlyCreatedKey]);

  return (
    <>
      <section className={sectionStyles['section']} aria-labelledby="api-keys-title" data-testid="api-keys-section">
        <header className={sectionStyles['section__header']}>
          <h2 id="api-keys-title" className={sectionStyles['section__title']}>
            {formatMessage({ id: 'integrations.api-keys-title' })}
          </h2>
          <Button
            className={sectionStyles['section__create-btn']}
            type="button"
            onClick={handleOpenCreateModal}
            size="sm"
            buttonStyle="yellow"
            label={formatMessage({ id: 'integrations.create-api-key' })}
            data-testid="create-api-key-btn"
          />
        </header>

        {isLoading && <TokenListItemSkeleton data-testid="api-keys-skeleton" />}

        {!isLoading && apiKeys.length === 0 && (
          <p className={sectionStyles['section__empty']} data-testid="empty-keys-message">
            {formatMessage({ id: 'integrations.no-api-keys' })}
          </p>
        )}

        {!isLoading && apiKeys.length > 0 && (
          <ul className={tokenListStyles['token-list']} data-testid="api-keys-list">
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
      <CreateApiKeyModal isOpen={isCreateModalOpen} onSubmit={handleCreate} onClose={handleCloseCreateModal} />
    </>
  );
}
