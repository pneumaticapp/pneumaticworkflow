import * as React from 'react';
import { useEffect, useState } from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  closeCreateAIProviderModal,
  createAIProvider,
  createAIProviderByVendor,
  loadAIVendors,
} from '../../../redux/ai/slice';
import {
  getAICreateProviderModalIsLoading,
  getAICreateProviderModalIsOpen,
  getAIProvidersList,
  getAIVendorsList,
} from '../../../redux/selectors/ai';
import { Button } from '../../UI/Buttons/Button';
import { FormikInputField } from '../../UI/Fields/InputField';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import { Tabs } from '../../UI/Tabs';
import { FormikDropdownList } from '../../UI/DropdownList';
import { ECreateAIProviderTab } from './types';
import type { ICreateAIProviderFormValues } from './types';
import { validateCreateAIProviderForm } from './utils/validateCreateAIProviderForm';

import styles from './AIProviders.css';

const INITIAL_VALUES: ICreateAIProviderFormValues = {
  vendor: '',
  name: '',
  baseUrl: '',
  apiKey: '',
};

export function CreateAIProviderModal() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isOpen = useSelector(getAICreateProviderModalIsOpen);
  const isCreating = useSelector(getAICreateProviderModalIsLoading);
  const vendors = useSelector(getAIVendorsList);
  const providers = useSelector(getAIProvidersList);

  const [activeTab, setActiveTab] = useState(ECreateAIProviderTab.Vendor);

  useEffect(() => {
    if (isOpen) {
      dispatch(loadAIVendors());
    }
  }, [isOpen, dispatch]);

  const handleClose = () => {
    dispatch(closeCreateAIProviderModal());
  };

  const handleChangeTab = (tab: ECreateAIProviderTab) => {
    if (!isCreating) setActiveTab(tab);
  };

  const handleSubmit = ({ vendor, name, baseUrl, apiKey }: ICreateAIProviderFormValues) => {
    if (activeTab === ECreateAIProviderTab.Vendor) {
      dispatch(createAIProviderByVendor({ vendor, apiKey: apiKey.trim() }));
    } else {
      dispatch(createAIProvider({ name: name.trim(), baseUrl: baseUrl.trim(), apiKey: apiKey.trim() }));
    }
  };

  const vendorOptions = vendors.map(({ slug, name: vendorName }) => ({ value: slug, label: vendorName }));
  const isVendorTab = activeTab === ECreateAIProviderTab.Vendor;

  const validateForm = (values: ICreateAIProviderFormValues) =>
    validateCreateAIProviderForm(values, activeTab, providers, vendors);

  return (
    <Modal isOpen={isOpen} onClose={handleClose} width="sm">
      <Header tag="h2" size="6" className={styles['create-modal__title']}>
        {formatMessage({ id: 'ai-providers.create-modal-title' })}
      </Header>
      <Tabs
        activeValueId={activeTab}
        values={[
          { id: ECreateAIProviderTab.Vendor, label: formatMessage({ id: 'ai-providers.tab-vendor' }) },
          { id: ECreateAIProviderTab.Custom, label: formatMessage({ id: 'ai-providers.tab-custom' }) },
        ]}
        variant="pill"
        containerClassName={styles['create-modal__tabs']}
        onChange={handleChangeTab}
      />
      <Formik
        key={activeTab}
        initialValues={INITIAL_VALUES}
        initialErrors={validateForm(INITIAL_VALUES)}
        validate={validateForm}
        onSubmit={handleSubmit}
      >
        {({ handleSubmit: formikSubmit, isValid }) => (
          <form onSubmit={formikSubmit} data-autofocus-first-field>
            <div className={styles['create-modal__fields']}>
              {isVendorTab ? (
                <>
                  <FormikDropdownList
                    name="vendor"
                    label={formatMessage({ id: 'ai-providers.vendor-label' })}
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
            <div className={styles['create-modal__footer']}>
              <Button
                type="submit"
                size="md"
                buttonStyle="yellow"
                disabled={!isValid || isCreating}
                isLoading={isCreating}
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
        )}
      </Formik>
    </Modal>
  );
}
