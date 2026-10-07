import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { createAIProvider, createAIProviderByVendor } from '../../../redux/ai/slice';
import { getIsAISaving } from '../../../redux/selectors/ai';
import { getAIVendors } from '../../../api/ai';
import { IAIVendor } from '../../../types/ai';
import { NotificationManager } from '../../UI/Notifications';
import { getErrorMessage } from '../../../utils/getErrorMessage';
import { logger } from '../../../utils/logger';
import { Button } from '../../UI/Buttons/Button';
import { InputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import { Tabs } from '../../UI/Tabs';
import { DropdownList } from '../../UI/DropdownList';

import styles from './AIProviders.css';

type TCreateTab = 'vendor' | 'custom';

interface ICreateAIProviderModalProps {
  isOpen: boolean;
  onClose(): void;
}

export function CreateAIProviderModal({ isOpen, onClose }: ICreateAIProviderModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isSaving = useSelector(getIsAISaving);

  const [activeTab, setActiveTab] = React.useState<TCreateTab>('vendor');
  const [vendors, setVendors] = React.useState<IAIVendor[]>([]);
  const [vendor, setVendor] = React.useState<string | null>(null);
  const [name, setName] = React.useState('');
  const [baseUrl, setBaseUrl] = React.useState('');
  const [apiKey, setApiKey] = React.useState('');

  React.useEffect(() => {
    if (!isOpen || vendors.length) {
      return;
    }

    let isCancelled = false;
    getAIVendors()
      .then((data) => {
        if (!isCancelled) {
          setVendors(data);
        }
      })
      .catch((error) => {
        NotificationManager.warning({ message: getErrorMessage(error) });
        logger.error('failed to load AI vendors', error);
      });

    return () => {
      isCancelled = true;
    };
  }, [isOpen, vendors.length]);

  const resetForm = React.useCallback(() => {
    setVendor(null);
    setName('');
    setBaseUrl('');
    setApiKey('');
  }, []);

  const handleClose = React.useCallback(() => {
    resetForm();
    onClose();
  }, [onClose, resetForm]);

  const handleTabChange = React.useCallback(
    (tabId: string | number) => {
      resetForm();
      setActiveTab(tabId as TCreateTab);
    },
    [resetForm],
  );

  const handleVendorChange = React.useCallback((option: { value?: string } | null) => {
    setVendor(option?.value ?? null);
  }, []);

  const handleSubmit = React.useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      if (activeTab === 'vendor') {
        if (!vendor || !apiKey.trim()) {
          return;
        }
        dispatch(createAIProviderByVendor({ vendor, apiKey: apiKey.trim() }));
      } else {
        if (!name.trim() || !baseUrl.trim() || !apiKey.trim()) {
          return;
        }
        dispatch(createAIProvider({ name: name.trim(), baseUrl: baseUrl.trim(), apiKey: apiKey.trim() }));
      }

      handleClose();
    },
    [activeTab, vendor, name, baseUrl, apiKey, dispatch, handleClose],
  );

  const vendorOptions = vendors.map(({ slug, name: vendorName }) => ({ value: slug, label: vendorName }));
  const isVendorTab = activeTab === 'vendor';
  const isSubmitDisabled = isVendorTab ? !vendor || !apiKey.trim() : !name.trim() || !baseUrl.trim() || !apiKey.trim();

  return (
    <Modal isOpen={isOpen} onClose={handleClose} width="sm">
      <div data-testid="create-ai-provider-modal">
        <Header tag="p" size="6" className={styles['create-modal__title']}>
          {formatMessage({ id: 'ai-providers.create-modal-title' })}
        </Header>
        <p className={styles['create-modal__description']}>
          {formatMessage({ id: 'ai-providers.create-modal-description' })}
        </p>
        <Tabs
          activeValueId={activeTab}
          values={[
            { id: 'vendor', label: formatMessage({ id: 'ai-providers.tab-vendor' }) },
            { id: 'custom', label: formatMessage({ id: 'ai-providers.tab-custom' }) },
          ]}
          containerClassName={styles['create-modal__tabs']}
          onChange={handleTabChange}
        />
        <form onSubmit={handleSubmit} data-autofocus-first-field>
          <div className={styles['create-modal__fields']}>
            {isVendorTab ? (
              <>
                <DropdownList
                  title={formatMessage({ id: 'ai-providers.vendor-label' })}
                  placeholder={formatMessage({ id: 'ai-providers.vendor-placeholder' })}
                  options={vendorOptions}
                  value={vendorOptions.find(({ value }) => value === vendor) ?? null}
                  onChange={handleVendorChange}
                  data-testid="ai-provider-vendor-select"
                />
                <InputField
                  title={formatMessage({ id: 'ai-providers.api-key-label' })}
                  value={apiKey}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiKey(e.target.value)}
                  placeholder={formatMessage({ id: 'ai-providers.api-key-placeholder' })}
                  fieldSize="md"
                  data-testid="ai-provider-api-key-input"
                />
              </>
            ) : (
              <>
                <InputField
                  autoFocus
                  title={formatMessage({ id: 'ai-providers.name-label' })}
                  value={name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                  placeholder={formatMessage({ id: 'ai-providers.name-placeholder' })}
                  fieldSize="md"
                  data-testid="ai-provider-name-input"
                />
                <InputField
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
              </>
            )}
          </div>
          <p className={styles['create-modal__info']}>{formatMessage({ id: 'ai-providers.connection-check-info' })}</p>
          <div className={styles['create-modal__footer']}>
            <Button
              type="submit"
              size="md"
              buttonStyle="yellow"
              disabled={isSubmitDisabled || isSaving}
              isLoading={isSaving}
              label={formatMessage({ id: 'ai-providers.add' })}
              data-testid="submit-create-ai-provider"
            />
            <button
              type="button"
              className="cancel-button"
              onClick={handleClose}
              data-testid="cancel-create-ai-provider"
            >
              {formatMessage({ id: 'integrations.cancel' })}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
