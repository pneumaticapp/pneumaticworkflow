import * as React from 'react';
import { useIntl, FormattedDate } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { IApiKeyItem } from '../../types/integrations';
import { IApplicationState } from '../../types/redux';
import { copyToClipboard } from '../../utils/helpers';
import { Button } from '../UI/Buttons/Button';
import { Modal } from '../UI/Modal/Modal';
import { EPageTitle } from '../../constants/defaultValues';
import { PageTitle } from '../PageTitle/PageTitle';
import {
  loadApiKeys,
  createApiKey,
  deleteApiKey,
  clearNewlyCreatedKey,
} from '../../redux/actions';

import styles from './IntegrationsCommon.css';

const KEY_MASK = '••••••••';

interface IApiKeyListItemProps {
  apiKey: IApiKeyItem;
  confirmDeleteId: number | null;
  onDelete: (id: number) => void;
  onConfirmDeleteStart: (id: number) => void;
  onConfirmDeleteCancel: () => void;
}

const ApiKeyListItem = React.memo(({
  apiKey,
  confirmDeleteId,
  onDelete,
  onConfirmDeleteStart,
  onConfirmDeleteCancel,
}: IApiKeyListItemProps) => {
  const { formatMessage } = useIntl();
  
  const handleDelete = React.useCallback(() => {
    onDelete(apiKey.id);
  }, [apiKey.id, onDelete]);

  const handleConfirmStart = React.useCallback(() => {
    onConfirmDeleteStart(apiKey.id);
  }, [apiKey.id, onConfirmDeleteStart]);

  return (
    <div className={styles['api-keys__item']} data-testid={`api-key-${apiKey.id}`}>
      <div className={styles['api-keys__item-info']}>
        <span className={styles['api-keys__item-name']}>{apiKey.name}</span>
        <span className={styles['api-keys__item-prefix']}>
          {apiKey.prefix}{KEY_MASK}
        </span>
        <span className={styles['api-keys__item-meta']}>
          {apiKey.lastUsedAt
            ? formatMessage(
              { id: 'integrations.api-key-last-used' },
              { date: <FormattedDate value={new Date(apiKey.lastUsedAt)} /> },
            )
            : formatMessage({ id: 'integrations.api-key-never-used' })
          }
        </span>
      </div>
      <div className={styles['api-keys__item-actions']}>
        {confirmDeleteId === apiKey.id ? (
          <div className={styles['api-keys__confirm-delete']}>
            <span className={styles['api-keys__confirm-text']}>
              {formatMessage({ id: 'integrations.delete-api-key-confirm' })}
            </span>
            <Button
              type="button"
              onClick={handleDelete}
              size="sm"
              buttonStyle="transparent-black"
              label={formatMessage({ id: 'integrations.api-key-revoke' })}
              data-testid={`confirm-revoke-${apiKey.id}`}
            />
            <Button
              type="button"
              onClick={onConfirmDeleteCancel}
              size="sm"
              buttonStyle="transparent-black"
              label={formatMessage({ id: 'integrations.cancel' })}
              data-testid={`cancel-revoke-${apiKey.id}`}
            />
          </div>
        ) : (
          <Button
            type="button"
            onClick={handleConfirmStart}
            size="sm"
            buttonStyle="transparent-black"
            label={formatMessage({ id: 'integrations.api-key-revoke' })}
            data-testid={`revoke-${apiKey.id}`}
          />
        )}
      </div>
    </div>
  );
});

export function IntegrationsCommon() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const apiKeys = useSelector(
    (state: IApplicationState) => state.integrations.apiKeys.data,
  );
  const isLoading = useSelector(
    (state: IApplicationState) => state.integrations.apiKeys.isLoading,
  );
  const newlyCreatedKey = useSelector(
    (state: IApplicationState) => state.integrations.apiKeys.newlyCreatedKey,
  );

  const [copied, setCopied] = React.useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = React.useState<number | null>(null);
  const [newKeyName, setNewKeyName] = React.useState('');
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const copyTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  React.useEffect(() => {
    dispatch(loadApiKeys());

    return () => {
      if (copyTimerRef.current) {
        clearTimeout(copyTimerRef.current);
      }
    };
  }, [dispatch]);

  const handleCopyKey = React.useCallback((text: string) => {
    copyToClipboard(text);
    setCopied(true);
    copyTimerRef.current = setTimeout(() => setCopied(false), 2000);
  }, []);

  const handleCreate = React.useCallback(() => {
    dispatch(createApiKey({ name: newKeyName || undefined }));
    setNewKeyName('');
    setShowCreateForm(false);
  }, [newKeyName, dispatch]);

  const handleDelete = React.useCallback((id: number) => {
    dispatch(deleteApiKey({ id }));
    setConfirmDeleteId(null);
  }, [dispatch]);

  const handleConfirmDeleteStart = React.useCallback((id: number) => {
    setConfirmDeleteId(id);
  }, []);

  const handleConfirmDeleteCancel = React.useCallback(() => {
    setConfirmDeleteId(null);
  }, []);

  const handleCloseNewKeyModal = React.useCallback(() => {
    dispatch(clearNewlyCreatedKey());
    setCopied(false);
  }, [dispatch]);

  const handleShowCreateForm = React.useCallback(() => {
    setShowCreateForm(true);
  }, []);

  const handleHideCreateForm = React.useCallback(() => {
    setShowCreateForm(false);
    setNewKeyName('');
  }, []);

  const handleCopyNewlyCreatedKey = React.useCallback(() => {
    handleCopyKey(newlyCreatedKey || '');
  }, [handleCopyKey, newlyCreatedKey]);

  const handleNameChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewKeyName(e.target.value);
    },
    [],
  );

  const supportEmail = formatMessage({ id: 'integrations.support-email' });
  const supportEmailLink = `mailto:${supportEmail}`;

  return (
    <>
      <PageTitle titleId={EPageTitle.Integrations} />
      <p className={styles['description']}>
        {formatMessage({ id: 'integrations.description' })}
      </p>

      <div className={styles['api-keys']} data-testid="api-keys-section">
        <div className={styles['api-keys__header']}>
          <p className={styles['api-keys__title']}>
            {formatMessage({ id: 'integrations.api-keys-title' })}
          </p>
          {!showCreateForm && (
            <Button
              className={styles['api-keys__create-btn']}
              type="button"
              onClick={handleShowCreateForm}
              size="sm"
              label={formatMessage({ id: 'integrations.create-api-key' })}
              data-testid="create-api-key-btn"
            />
          )}
        </div>

        {showCreateForm && (
          <div className={styles['api-keys__create-form']} data-testid="create-key-form">
            <input
              className={styles['api-keys__name-input']}
              type="text"
              value={newKeyName}
              onChange={handleNameChange}
              placeholder={formatMessage({ id: 'integrations.api-key-name-placeholder' })}
              data-testid="api-key-name-input"
            />
            <div className={styles['api-keys__create-actions']}>
              <Button
                type="button"
                onClick={handleCreate}
                size="sm"
                label={formatMessage({ id: 'integrations.create-api-key' })}
                data-testid="submit-create-key"
              />
              <Button
                type="button"
                onClick={handleHideCreateForm}
                size="sm"
                buttonStyle="transparent-black"
                label={formatMessage({ id: 'integrations.cancel' })}
                data-testid="cancel-create-key"
              />
            </div>
          </div>
        )}

        {isLoading && (
          <p className={styles['api-keys__loading']}>
            {formatMessage({ id: 'integrations.loading-api-key' })}
          </p>
        )}

        {!isLoading && apiKeys.length === 0 && (
          <p className={styles['api-keys__empty']} data-testid="empty-keys-message">
            {formatMessage({ id: 'integrations.no-api-keys' })}
          </p>
        )}

        {!isLoading && apiKeys.length > 0 && (
          <div className={styles['api-keys__list']} data-testid="api-keys-list">
            {apiKeys.map((key: IApiKeyItem) => (
              <ApiKeyListItem
                key={key.id}
                apiKey={key}
                confirmDeleteId={confirmDeleteId}
                onDelete={handleDelete}
                onConfirmDeleteStart={handleConfirmDeleteStart}
                onConfirmDeleteCancel={handleConfirmDeleteCancel}
              />
            ))}
          </div>
        )}
      </div>

      {/* Newly created key modal */}
      <Modal isOpen={!!newlyCreatedKey} onClose={handleCloseNewKeyModal} width="sm">
        <div data-testid="new-key-modal" className={styles['api-keys__modal-content']}>
          <p className={styles['api-keys__modal-title']}>
            {formatMessage({ id: 'integrations.api-key-created-title' })}
          </p>
          <p className={styles['api-keys__modal-warning']}>
            {formatMessage({ id: 'integrations.api-key-created-warning' })}
          </p>
          <div className={styles['api-keys__modal-key']}>
            <code
              className={styles['api-keys__modal-key-value']}
              data-testid="raw-key-value"
            >
              {newlyCreatedKey}
            </code>
          </div>
          <div className={styles['api-keys__modal-actions']}>
            <Button
              type="button"
              onClick={handleCopyNewlyCreatedKey}
              size="sm"
              label={copied
                ? formatMessage({ id: 'integrations.api-key-copied' })
                : formatMessage({ id: 'integrations.api-key-copy' })
              }
              data-testid="copy-key-btn"
            />
            <Button
              type="button"
              onClick={handleCloseNewKeyModal}
              size="sm"
              buttonStyle="transparent-black"
              label={formatMessage({ id: 'integrations.api-key-done' })}
              data-testid="done-key-btn"
            />
          </div>
        </div>
      </Modal>

      <p className={styles['hint']}>
        {formatMessage({ id: 'integrations.hint' })}
        <a className={styles['link']} href={supportEmailLink}>{supportEmail}</a>
      </p>
    </>
  );
}
