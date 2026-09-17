import * as React from 'react';
import { useIntl, FormattedDate } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { IApiKeyItem } from '../../types/integrations';
import { IApplicationState } from '../../types/redux';
import { copyToClipboard } from '../../utils/helpers';
import { Button } from '../UI/Buttons/Button';
import { InputField } from '../UI/Fields/InputField';
import { Header } from '../UI/Typeography/Header';
import { Modal } from '../UI/Modal/Modal';
import { NotificationManager } from '../UI/Notifications';
import { EPageTitle } from '../../constants/defaultValues';
import { PageTitle } from '../PageTitle/PageTitle';
import { loadApiKeys, createApiKey, deleteApiKey, clearNewlyCreatedKey } from '../../redux/actions';

import styles from './IntegrationsCommon.css';

const KEY_MASK = '••••••••';

interface IApiKeyListItemProps {
  apiKey: IApiKeyItem;
  onRevoke: (id: number) => void;
}

const ApiKeyListItem = React.memo(({ apiKey, onRevoke }: IApiKeyListItemProps) => {
  const { formatMessage } = useIntl();

  const handleRevoke = React.useCallback(() => {
    onRevoke(apiKey.id);
  }, [apiKey.id, onRevoke]);

  return (
    <div className={styles['api-keys__item']} data-testid={`api-key-${apiKey.id}`}>
      <div className={styles['api-keys__item-info']}>
        <span className={styles['api-keys__item-name']}>{apiKey.name}</span>
        <span className={styles['api-keys__item-prefix']}>
          {apiKey.prefix}
          {KEY_MASK}
        </span>
        <span className={styles['api-keys__item-meta']}>
          {apiKey.lastUsedAt
            ? formatMessage(
                { id: 'integrations.api-key-last-used' },
                { date: <FormattedDate value={new Date(apiKey.lastUsedAt)} /> },
              )
            : formatMessage({ id: 'integrations.api-key-never-used' })}
        </span>
      </div>
      <div className={styles['api-keys__item-actions']}>
        <Button
          type="button"
          onClick={handleRevoke}
          size="sm"
          buttonStyle="transparent-black"
          label={formatMessage({ id: 'integrations.api-key-revoke' })}
          data-testid={`revoke-${apiKey.id}`}
        />
      </div>
    </div>
  );
});
ApiKeyListItem.displayName = 'ApiKeyListItem';

export function IntegrationsCommon() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const apiKeys = useSelector((state: IApplicationState) => state.integrations.apiKeys.data);
  const isLoading = useSelector((state: IApplicationState) => state.integrations.apiKeys.isLoading);
  const newlyCreatedKey = useSelector((state: IApplicationState) => state.integrations.apiKeys.newlyCreatedKey);

  const [confirmDeleteId, setConfirmDeleteId] = React.useState<number | null>(null);
  const [newKeyName, setNewKeyName] = React.useState('');
  const [showCreateForm, setShowCreateForm] = React.useState(false);

  React.useEffect(() => {
    dispatch(loadApiKeys());

    return () => {
      dispatch(clearNewlyCreatedKey());
    };
  }, [dispatch]);

  const handleCreate = React.useCallback(() => {
    dispatch(createApiKey({ name: newKeyName || undefined }));
    setNewKeyName('');
    setShowCreateForm(false);
  }, [newKeyName, dispatch]);

  const handleCreateSubmit = React.useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      handleCreate();
    },
    [handleCreate],
  );

  const handleDelete = React.useCallback(() => {
    if (confirmDeleteId !== null) {
      dispatch(deleteApiKey({ id: confirmDeleteId }));
      setConfirmDeleteId(null);
    }
  }, [confirmDeleteId, dispatch]);

  const handleConfirmDeleteStart = React.useCallback((id: number) => {
    setConfirmDeleteId(id);
  }, []);

  const handleConfirmDeleteCancel = React.useCallback(() => {
    setConfirmDeleteId(null);
  }, []);

  const handleCloseNewKeyModal = React.useCallback(() => {
    dispatch(clearNewlyCreatedKey());
  }, [dispatch]);

  const handleShowCreateForm = React.useCallback(() => {
    setShowCreateForm(true);
  }, []);

  const handleHideCreateForm = React.useCallback(() => {
    setShowCreateForm(false);
    setNewKeyName('');
  }, []);

  const handleCopyNewlyCreatedKey = React.useCallback(() => {
    if (newlyCreatedKey) {
      copyToClipboard(newlyCreatedKey);
      NotificationManager.success({ message: 'integrations.api-key-copied' });
    }
  }, [newlyCreatedKey]);

  const handleNameChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setNewKeyName(e.target.value);
  }, []);

  const supportEmail = formatMessage({ id: 'integrations.support-email' });
  const supportEmailLink = `mailto:${supportEmail}`;

  return (
    <>
      <PageTitle titleId={EPageTitle.Integrations} />
      <p className={styles['description']}>{formatMessage({ id: 'integrations.description' })}</p>

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
            {apiKeys.map((key: IApiKeyItem) => (
              <ApiKeyListItem key={key.id} apiKey={key} onRevoke={handleConfirmDeleteStart} />
            ))}
          </div>
        )}
      </div>

      {/* Newly created key modal */}
      <Modal isOpen={!!newlyCreatedKey} onClose={handleCloseNewKeyModal} width="sm">
        <div data-testid="new-key-modal">
          <Header tag="p" size="6" className={styles['create-modal__title']}>
            {formatMessage({ id: 'integrations.api-key-created-title' })}
          </Header>
          <p className={styles['api-keys__modal-warning']}>
            {formatMessage({ id: 'integrations.api-key-created-warning' })}
          </p>
          <div className={styles['api-keys__modal-key']}>
            <code className={styles['api-keys__modal-key-value']} data-testid="raw-key-value">
              {newlyCreatedKey}
            </code>
            <button
              type="button"
              className={styles['api-keys__modal-copy-btn']}
              onClick={handleCopyNewlyCreatedKey}
              data-testid="copy-inline-btn"
            >
              {formatMessage({ id: 'team.create-user-modal.copy' })}
            </button>
          </div>
          <div className={styles['create-modal__footer']}>
            <Button
              type="button"
              onClick={handleCloseNewKeyModal}
              size="md"
              label={formatMessage({ id: 'integrations.api-key-done' })}
              data-testid="done-key-btn"
            />
          </div>
        </div>
      </Modal>

      {/* Revoke confirmation modal */}
      <Modal isOpen={confirmDeleteId !== null} onClose={handleConfirmDeleteCancel} width="sm">
        <div data-testid="revoke-key-modal">
          <Header tag="p" size="6" className={styles['create-modal__title']}>
            {formatMessage({ id: 'integrations.revoke-modal-title' })}
          </Header>
          <p className={styles['api-keys__modal-warning']}>
            {formatMessage({ id: 'integrations.delete-api-key-confirm' })}
          </p>
          <div className={styles['create-modal__footer']}>
            <Button
              type="button"
              onClick={handleDelete}
              size="md"
              buttonStyle="yellow"
              label={formatMessage({ id: 'integrations.api-key-revoke' })}
              data-testid="confirm-revoke-btn"
            />
            <button
              type="button"
              className="cancel-button"
              onClick={handleConfirmDeleteCancel}
              data-testid="cancel-revoke-btn"
            >
              {formatMessage({ id: 'integrations.cancel' })}
            </button>
          </div>
        </div>
      </Modal>

      {/* Create API Key modal */}
      <Modal isOpen={showCreateForm} onClose={handleHideCreateForm} width="sm">
        <div data-testid="create-key-modal">
          <Header tag="p" size="6" className={styles['create-modal__title']}>
            {formatMessage({ id: 'integrations.create-api-key-modal-title' })}
          </Header>
          <p className={styles['create-modal__description']}>
            {formatMessage({ id: 'integrations.create-api-key-modal-description' })}
          </p>
          <form onSubmit={handleCreateSubmit} data-autofocus-first-field>
            <InputField
              autoFocus
              value={newKeyName}
              onChange={handleNameChange}
              placeholder={formatMessage({ id: 'integrations.api-key-name-placeholder' })}
              fieldSize="md"
              data-testid="api-key-name-input"
            />
            <div className={styles['create-modal__footer']}>
              <Button
                type="submit"
                size="md"
                buttonStyle="yellow"
                label={formatMessage({ id: 'integrations.create-api-key' })}
                data-testid="submit-create-key"
              />
              <button
                type="button"
                className="cancel-button"
                onClick={handleHideCreateForm}
                data-testid="cancel-create-key"
              >
                {formatMessage({ id: 'integrations.cancel' })}
              </button>
            </div>
          </form>
        </div>
      </Modal>

      <p className={styles['hint']}>
        {formatMessage({ id: 'integrations.hint' })}
        <a className={styles['link']} href={supportEmailLink}>
          {supportEmail}
        </a>
      </p>
    </>
  );
}
