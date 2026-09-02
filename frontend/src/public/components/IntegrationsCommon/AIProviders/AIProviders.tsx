import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { IAIProvider } from '../../../types/ai';
import { Button } from '../../UI/Buttons/Button';
import { InputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import { Tooltip } from '../../UI';
import { createAIProvider, deleteAIProvider, loadAIProviders } from '../../../redux/ai/slice';
import { getAIProvidersState, getIsAISaving } from '../../../redux/selectors/ai';

import styles from './AIProviders.css';

const KEY_MASK = '••••••••';

interface IAIProviderListItemProps {
  provider: IAIProvider;
  onDelete: (id: number) => void;
}

const AIProviderListItem = React.memo(({ provider, onDelete }: IAIProviderListItemProps) => {
  const { formatMessage } = useIntl();
  const isUsed = provider.usage.length > 0;

  const handleDelete = React.useCallback(() => {
    onDelete(provider.id);
  }, [provider.id, onDelete]);

  const deleteButton = (
    <Button
      type="button"
      onClick={handleDelete}
      size="sm"
      buttonStyle="transparent-black"
      disabled={isUsed}
      label={formatMessage({ id: 'ai-providers.delete' })}
      data-testid={`delete-ai-provider-${provider.id}`}
    />
  );

  return (
    <div className={styles['providers__item']} data-testid={`ai-provider-${provider.id}`}>
      <div className={styles['providers__item-info']}>
        <span className={styles['providers__item-name']}>{provider.name}</span>
        <span className={styles['providers__item-url']}>{provider.baseUrl}</span>
        <span className={styles['providers__item-key']}>
          {provider.apiKeyPrefix}
          {KEY_MASK}
        </span>
        {isUsed && (
          <span className={styles['providers__item-usage']} data-testid={`ai-provider-usage-${provider.id}`}>
            {formatMessage(
              { id: 'ai-providers.usage' },
              { agents: provider.usage.map(({ name }) => name).join(', ') },
            )}
          </span>
        )}
      </div>
      <div className={styles['providers__item-actions']}>
        {isUsed ? (
          <Tooltip
            content={formatMessage(
              { id: 'ai-providers.delete-disabled-tooltip' },
              { agents: provider.usage.map(({ name }) => name).join(', ') },
            )}
          >
            {/* A disabled button swallows pointer events, so the tooltip hangs on the wrapper. */}
            <div data-testid={`delete-ai-provider-guard-${provider.id}`}>{deleteButton}</div>
          </Tooltip>
        ) : (
          deleteButton
        )}
      </div>
    </div>
  );
});
AIProviderListItem.displayName = 'AIProviderListItem';

export function AIProviders() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const { list: providers, isLoading, isLoaded } = useSelector(getAIProvidersState);
  const isSaving = useSelector(getIsAISaving);

  const [confirmDeleteId, setConfirmDeleteId] = React.useState<number | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const [baseUrl, setBaseUrl] = React.useState('');
  const [apiKey, setApiKey] = React.useState('');

  React.useEffect(() => {
    dispatch(loadAIProviders());
  }, [dispatch]);

  const resetCreateForm = React.useCallback(() => {
    setIsCreateModalOpen(false);
    setBaseUrl('');
    setApiKey('');
  }, []);

  const handleCreateSubmit = React.useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      if (!baseUrl.trim() || !apiKey.trim()) {
        return;
      }

      dispatch(createAIProvider({ baseUrl: baseUrl.trim(), apiKey: apiKey.trim() }));
      resetCreateForm();
    },
    [baseUrl, apiKey, dispatch, resetCreateForm],
  );

  const handleDelete = React.useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteAIProvider(confirmDeleteId));
      setConfirmDeleteId(null);
    }
  }, [confirmDeleteId, dispatch]);

  const providerToDelete = providers.find(({ id }) => id === confirmDeleteId);

  return (
    <div className={styles['providers']} data-testid="ai-providers-section">
      <div className={styles['providers__header']}>
        <p className={styles['providers__title']}>{formatMessage({ id: 'ai-providers.title' })}</p>
        <Button
          className={styles['providers__create-btn']}
          type="button"
          onClick={() => setIsCreateModalOpen(true)}
          size="sm"
          buttonStyle="yellow"
          label={formatMessage({ id: 'ai-providers.add' })}
          data-testid="create-ai-provider-btn"
        />
      </div>

      {isLoading && !isLoaded && (
        <p className={styles['providers__loading']}>{formatMessage({ id: 'ai-providers.loading' })}</p>
      )}

      {isLoaded && providers.length === 0 && (
        <p className={styles['providers__empty']} data-testid="empty-ai-providers-message">
          {formatMessage({ id: 'ai-providers.empty' })}
        </p>
      )}

      {providers.length > 0 && (
        <div className={styles['providers__list']} data-testid="ai-providers-list">
          {providers.map((provider) => (
            <AIProviderListItem key={provider.id} provider={provider} onDelete={setConfirmDeleteId} />
          ))}
        </div>
      )}

      {/* Create AI provider modal */}
      <Modal isOpen={isCreateModalOpen} onClose={resetCreateForm} width="sm">
        <div data-testid="create-ai-provider-modal">
          <Header tag="p" size="6" className={styles['create-modal__title']}>
            {formatMessage({ id: 'ai-providers.create-modal-title' })}
          </Header>
          <p className={styles['create-modal__description']}>
            {formatMessage({ id: 'ai-providers.create-modal-description' })}
          </p>
          <form onSubmit={handleCreateSubmit} data-autofocus-first-field>
            <div className={styles['create-modal__fields']}>
              <InputField
                autoFocus
                title={formatMessage({ id: 'ai-providers.base-url-label' })}
                value={baseUrl}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBaseUrl(e.target.value)}
                placeholder={formatMessage({ id: 'ai-providers.base-url-placeholder' })}
                fieldSize="md"
                data-testid="ai-provider-base-url-input"
              />
              <InputField
                title={formatMessage({ id: 'ai-providers.api-key-label' })}
                value={apiKey}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiKey(e.target.value)}
                placeholder={formatMessage({ id: 'ai-providers.api-key-placeholder' })}
                fieldSize="md"
                data-testid="ai-provider-api-key-input"
              />
            </div>
            <div className={styles['create-modal__footer']}>
              <Button
                type="submit"
                size="md"
                buttonStyle="yellow"
                disabled={!baseUrl.trim() || !apiKey.trim() || isSaving}
                isLoading={isSaving}
                label={formatMessage({ id: 'ai-providers.add' })}
                data-testid="submit-create-ai-provider"
              />
              <button type="button" className="cancel-button" onClick={resetCreateForm} data-testid="cancel-create-ai-provider">
                {formatMessage({ id: 'integrations.cancel' })}
              </button>
            </div>
          </form>
        </div>
      </Modal>

      {/* Delete confirmation modal */}
      <Modal isOpen={confirmDeleteId !== null} onClose={() => setConfirmDeleteId(null)} width="sm">
        <div data-testid="delete-ai-provider-modal">
          <Header tag="p" size="6" className={styles['create-modal__title']}>
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
    </div>
  );
}
