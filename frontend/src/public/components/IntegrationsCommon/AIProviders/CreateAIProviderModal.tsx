import * as React from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { createAIProvider, createAIProviderByVendor, loadAIVendors } from '../../../redux/ai/slice';
import { getAICreateProviderState, getAIVendorsState, getIsAISaving } from '../../../redux/selectors/ai';
import { getErrorsObject } from '../../../utils/formik/getErrorsObject';
import { validateRequired } from '../../../utils/validators';
import { Button } from '../../UI/Buttons/Button';
import { FormikInputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import { Tabs } from '../../UI/Tabs';
import { FormikDropdownList } from '../../UI/DropdownList';
import type { ICreateAIProviderModalProps, ICreateAIProviderFormValues } from './types';

import styles from './AIProviders.css';

type TCreateTab = 'vendor' | 'custom';

const INITIAL_VALUES: ICreateAIProviderFormValues = {
  vendor: '',
  name: '',
  baseUrl: '',
  apiKey: '',
};

export function CreateAIProviderModal({ isOpen, onClose }: ICreateAIProviderModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isSaving = useSelector(getIsAISaving);
  const createProviderState = useSelector(getAICreateProviderState);
  const { list: vendors } = useSelector(getAIVendorsState);

  const [activeTab, setActiveTab] = React.useState<TCreateTab>('vendor');
  const [pendingRequestId, setPendingRequestId] = React.useState<number | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      dispatch(loadAIVendors());
    }
  }, [isOpen, dispatch]);

  React.useEffect(() => {
    if (!isOpen) setPendingRequestId(null);
  }, [isOpen]);

  React.useEffect(() => {
    if (
      isOpen &&
      pendingRequestId !== null &&
      createProviderState.requestId === pendingRequestId &&
      createProviderState.status === 'succeeded'
    ) {
      onClose();
    }
  }, [isOpen, pendingRequestId, createProviderState, onClose]);

  const handleSubmit = ({ vendor, name, baseUrl, apiKey }: ICreateAIProviderFormValues) => {
    if (activeTab === 'vendor') {
      const action = createAIProviderByVendor({ vendor, apiKey: apiKey.trim() });
      setPendingRequestId(action.meta.requestId);
      dispatch(action);
    } else {
      const action = createAIProvider({ name: name.trim(), baseUrl: baseUrl.trim(), apiKey: apiKey.trim() });
      setPendingRequestId(action.meta.requestId);
      dispatch(action);
    }
  };

  const vendorOptions = vendors.map(({ slug, name: vendorName }) => ({ value: slug, label: vendorName }));
  const isVendorTab = activeTab === 'vendor';
  const isCreating =
    pendingRequestId !== null &&
    (createProviderState.requestId !== pendingRequestId || createProviderState.status !== 'failed');

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="sm">
      <div data-testid="create-ai-provider-modal">
        <Header tag="h2" size="6" className={styles['create-modal__title']}>
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
          activeTabClassName={styles['create-modal__tab_active']}
          onChange={(tabId) => {
            if (!isCreating) setActiveTab(tabId as TCreateTab);
          }}
        />
        <Formik
          key={activeTab}
          initialValues={INITIAL_VALUES}
          validateOnMount
          validate={(values) =>
            getErrorsObject(
              values,
              isVendorTab
                ? { vendor: validateRequired, apiKey: validateRequired }
                : { name: validateRequired, baseUrl: validateRequired, apiKey: validateRequired },
            )
          }
          onSubmit={handleSubmit}
        >
          {({ handleSubmit: formikSubmit, isValid }) => (
            <form onSubmit={formikSubmit} data-autofocus-first-field>
              <div className={styles['create-modal__fields']}>
                {isVendorTab ? (
                  <>
                    <FormikDropdownList
                      name="vendor"
                      title={formatMessage({ id: 'ai-providers.vendor-label' })}
                      placeholder={formatMessage({ id: 'ai-providers.vendor-placeholder' })}
                      options={vendorOptions}
                      isRequired
                      data-testid="ai-provider-vendor-select"
                    />
                    <FormikInputField
                      name="apiKey"
                      title={formatMessage({ id: 'ai-providers.api-key-label' })}
                      placeholder={formatMessage({ id: 'ai-providers.api-key-placeholder' })}
                      fieldSize="md"
                      type="password"
                      isRequired
                      data-testid="ai-provider-api-key-input"
                    />
                  </>
                ) : (
                  <>
                    <FormikInputField
                      autoFocus
                      name="name"
                      title={formatMessage({ id: 'ai-providers.name-label' })}
                      placeholder={formatMessage({ id: 'ai-providers.name-placeholder' })}
                      fieldSize="md"
                      isRequired
                      data-testid="ai-provider-name-input"
                    />
                    <FormikInputField
                      name="baseUrl"
                      title={formatMessage({ id: 'ai-providers.base-url-label' })}
                      placeholder={formatMessage({ id: 'ai-providers.base-url-placeholder' })}
                      fieldSize="md"
                      isRequired
                      data-testid="ai-provider-base-url-input"
                    />
                    <FormikInputField
                      name="apiKey"
                      title={formatMessage({ id: 'ai-providers.api-key-label' })}
                      placeholder={formatMessage({ id: 'ai-providers.api-key-placeholder' })}
                      fieldSize="md"
                      type="password"
                      isRequired
                      data-testid="ai-provider-api-key-input"
                    />
                  </>
                )}
              </div>
              <p className={styles['create-modal__info']}>
                {formatMessage({ id: 'ai-providers.connection-check-info' })}
              </p>
              <div className={styles['create-modal__footer']}>
                <Button
                  type="submit"
                  size="md"
                  buttonStyle="yellow"
                  disabled={!isValid || isSaving || isCreating}
                  isLoading={isCreating}
                  label={formatMessage({ id: 'ai-providers.add' })}
                  data-testid="submit-create-ai-provider"
                />
                <button
                  type="button"
                  className="cancel-button"
                  onClick={onClose}
                  data-testid="cancel-create-ai-provider"
                >
                  {formatMessage({ id: 'integrations.cancel' })}
                </button>
              </div>
            </form>
          )}
        </Formik>
      </div>
    </Modal>
  );
}
