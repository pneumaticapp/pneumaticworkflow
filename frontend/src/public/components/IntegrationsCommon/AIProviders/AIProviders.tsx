import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../../UI/Buttons/Button';
import { WarningPopup } from '../../UI/WarningPopup';
import { TokenListItemSkeleton } from '../TokenListItem';
import { deleteAIProvider, loadAIProviders, openCreateAIProviderModal } from '../../../redux/ai/slice';
import { getAIProvidersIsLoading, getAIProvidersList } from '../../../redux/selectors/ai';

import { CreateAIProviderModal } from './CreateAIProviderModal';
import { AIProviderListItem } from './AIProviderListItem';
import sectionStyles from '../IntegrationsCommon.css';
import tokenListStyles from '../TokenListItem/TokenListItem.css';

export function AIProviders() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const providers = useSelector(getAIProvidersList);
  const isLoading = useSelector(getAIProvidersIsLoading);

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  useEffect(() => {
    dispatch(loadAIProviders());
  }, [dispatch]);

  const handleDelete = useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteAIProvider(confirmDeleteId));
    }
  }, [confirmDeleteId, dispatch]);

  const handleCloseDeleteModal = useCallback(() => setConfirmDeleteId(null), []);

  const handleOpenCreateModal = () => {
    dispatch(openCreateAIProviderModal());
  };

  const providerToDelete = providers.find(({ id }) => id === confirmDeleteId);

  return (
    <section
      className={sectionStyles['section']}
      aria-labelledby="ai-providers-title"
      data-testid="ai-providers-section"
    >
      <header className={sectionStyles['section__header']}>
        <h2 id="ai-providers-title" className={sectionStyles['section__title']}>
          {formatMessage({ id: 'ai-providers.title' })}
        </h2>
        <Button
          className={sectionStyles['section__create-btn']}
          type="button"
          onClick={handleOpenCreateModal}
          size="sm"
          buttonStyle="yellow"
          label={formatMessage({ id: 'ai-providers.add' })}
          data-testid="create-ai-provider-btn"
        />
      </header>

      {isLoading && <TokenListItemSkeleton data-testid="ai-providers-skeleton" />}

      {!isLoading && providers.length === 0 && (
        <p className={sectionStyles['section__empty']} data-testid="empty-ai-providers-message">
          {formatMessage({ id: 'ai-providers.empty' })}
        </p>
      )}

      {providers.length > 0 && (
        <ul className={tokenListStyles['token-list']} data-testid="ai-providers-list">
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
        onReject={handleCloseDeleteModal}
        closeModal={handleCloseDeleteModal}
      />
    </section>
  );
}
