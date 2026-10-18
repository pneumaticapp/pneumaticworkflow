import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../../UI/Buttons/Button';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
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

  const [confirmDeleteId, setConfirmDeleteId] = React.useState<number | null>(null);

  React.useEffect(() => {
    dispatch(loadAIProviders());
  }, [dispatch]);

  const handleDelete = React.useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteAIProvider(confirmDeleteId));
      setConfirmDeleteId(null);
    }
  }, [confirmDeleteId, dispatch]);

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

      <Modal isOpen={confirmDeleteId !== null} onClose={() => setConfirmDeleteId(null)} width="sm">
        <div data-testid="delete-ai-provider-modal">
          <Header tag="h2" size="6" className={styles['create-modal__title']}>
            {formatMessage({ id: 'ai-providers.delete-modal-title' })}
          </Header>
          <p className={styles['create-modal__warning']}>
            {formatMessage({ id: 'ai-providers.delete-confirm' }, { name: providerToDelete?.name ?? '' })}
          </p>
          <div className={styles['create-modal__footer']}>
            <Button
              type="button"
              onClick={handleDelete}
              size="md"
              buttonStyle="yellow"
              label={formatMessage({ id: 'ai-providers.delete' })}
              data-testid="confirm-delete-ai-provider"
            />
            <button
              type="button"
              className="cancel-button"
              onClick={() => setConfirmDeleteId(null)}
              data-testid="cancel-delete-ai-provider"
            >
              {formatMessage({ id: 'integrations.cancel' })}
            </button>
          </div>
        </div>
      </Modal>
    </section>
  );
}
