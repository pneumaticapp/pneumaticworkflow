import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../../UI/Buttons/Button';
import { WarningPopup } from '../../UI/WarningPopup';
import { deleteAIProvider, loadAIProviders, openCreateAIProviderModal } from '../../../redux/ai/slice';
import { getAIProvidersState } from '../../../redux/selectors/ai';

import { CreateAIProviderModal } from './CreateAIProviderModal';
import { AIProvidersSkeleton } from './AIProvidersSkeleton';
import { AIProviderListItem } from './AIProviderListItem';
import styles from './AIProviders.css';

export function AIProviders() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const { list: providers, isLoading } = useSelector(getAIProvidersState);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  useEffect(() => {
    dispatch(loadAIProviders());
  }, [dispatch]);

  const handleDelete = useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteAIProvider(confirmDeleteId));
    }
  }, [confirmDeleteId, dispatch]);

  const closeDeleteModal = useCallback(() => setConfirmDeleteId(null), []);

  const providerToDelete = providers.find(({ id }) => id === confirmDeleteId);

  return (
    <section className={styles['providers']} aria-labelledby="ai-providers-title" data-testid="ai-providers-section">
      <header className={styles['providers__header']}>
        <h2 id="ai-providers-title" className={styles['providers__title']}>
          {formatMessage({ id: 'ai-providers.title' })}
        </h2>
        <Button
          className={styles['providers__create-btn']}
          type="button"
          onClick={() => dispatch(openCreateAIProviderModal())}
          size="sm"
          buttonStyle="yellow"
          label={formatMessage({ id: 'ai-providers.add' })}
          data-testid="create-ai-provider-btn"
        />
      </header>

      {isLoading && <AIProvidersSkeleton />}

      {!isLoading && providers.length === 0 && (
        <p className={styles['providers__empty']} data-testid="empty-ai-providers-message">
          {formatMessage({ id: 'ai-providers.empty' })}
        </p>
      )}

      {providers.length > 0 && (
        <ul className={styles['providers__list']} data-testid="ai-providers-list">
          {providers.map((provider) => (
            <AIProviderListItem key={provider.id} provider={provider} onDelete={setConfirmDeleteId} />
          ))}
        </ul>
      )}

      <CreateAIProviderModal />

      <WarningPopup
        isOpen={confirmDeleteId !== null}
        title={formatMessage({ id: 'ai-providers.delete-modal-title' })}
        message={formatMessage({ id: 'ai-providers.delete-confirm' }, { name: providerToDelete?.name ?? '' })}
        acceptTitle={formatMessage({ id: 'ai-providers.delete' })}
        declineTitle={formatMessage({ id: 'integrations.cancel' })}
        onConfirm={handleDelete}
        onReject={closeDeleteModal}
        closeModal={closeDeleteModal}
      />
    </section>
  );
}
