import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';

import { validateTenantName } from '../../../utils/validators';
import { TChangeTenantNamePayload } from '../../../redux/actions';
import { Button, Header, InputField, Modal } from '../../UI';
import {
  ELearnMoreLinks,
  PRICE_UNLIMITED_USER_IN_USD_ANN,
  PRICE_UNLIMITED_USER_IN_USD_MO,
} from '../../../constants/defaultValues';
import { ETypeTenantModal, ITenant } from '../../../types/tenants';

import styles from './TenantModal.css';

export function TenantModal({ stateModal, createTenant, changeNameTenant, closeModal }: ITenantModalProps) {
  const { formatMessage } = useIntl();

  const { isOpen, type } = stateModal;
  const id = 'id' in stateModal ? stateModal.id : -1;

  let name = 'tenantName' in stateModal ? stateModal.tenantName : '';
  if (type === ETypeTenantModal.Create) {
    name = formatMessage({ id: 'tenants.modal-add-name-default' });
  }

  const [inputName, setInputName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setInputName(name);
  }, [name]);

  const validationForm = () => {
    const currentError = validateTenantName(inputName);
    if (currentError) {
      setError(currentError);
      return false;
    }

    return true;
  };

  const handleCloseModal = () => {
    closeModal();
    setError('');
  };

  const handleCreateTenant = () => {
    if (!validationForm()) return;
    createTenant(inputName);
    setInputName('');
    handleCloseModal();
  };

  const handleChangeNameTenant = ({ id: currentId, tenantName: currentName }: Pick<ITenant, 'id' | 'tenantName'>) => {
    if (!validationForm()) return;
    changeNameTenant({ id: currentId, name: currentName });
    handleCloseModal();
  };

  const data: { [key in ETypeTenantModal]: IDataTenantModal } = {
    [ETypeTenantModal.Create]: {
      title: formatMessage({ id: 'tenants.modal-title-create' }),
      description: formatMessage({ id: 'tenants.modal-description-create' }),
      footnote: formatMessage(
        { id: 'tenants.modal-footnote-create' },
        {
          priceUnlimitedMO: PRICE_UNLIMITED_USER_IN_USD_MO,
          priceUnlimitedANN: PRICE_UNLIMITED_USER_IN_USD_ANN,
        },
      ),
      button: formatMessage({ id: 'tenants.modal-button-create' }),
      action: (e) => {
        e.preventDefault();
        handleCreateTenant();
      },
    },
    [ETypeTenantModal.EditName]: {
      title: formatMessage({ id: 'tenants.modal-title-edit' }),
      description: formatMessage({ id: 'tenants.modal-description-create' }),
      button: formatMessage({ id: 'tenants.modal-button-edit' }),
      action: (e) => {
        e.preventDefault();
        handleChangeNameTenant({ id, tenantName: inputName });
      },
    },
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['tenant-modal__title']}>
          {data[type].title}
        </Header>
        <p className={styles['tenant-modal__description']}>
          {data[type].description}&nbsp;
          <a target="_blank" rel="noreferrer" href={ELearnMoreLinks.TenantsModal}>
            {formatMessage({ id: 'tenants.modal-description-learn-more' })}
          </a>
        </p>
        <p className={styles['tenant-modal__footnote']}>{data[type].footnote}</p>
        <form onSubmit={(e) => data[type].action(e)} data-autofocus-first-field>
          <InputField
            autoFocus
            value={inputName}
            onChange={(e) => setInputName(e.currentTarget.value)}
            errorMessage={error}
            fieldSize="md"
            placeholder={formatMessage({ id: 'tenants.modal-add-name-placeholder' })}
          />
          <div className={styles['tenant-modal__footer']}>
            <Button type="submit" label={data[type].button} buttonStyle="yellow" size="md" disabled={!inputName} />
            <button type="button" className="cancel-button" onClick={handleCloseModal}>
              {formatMessage({ id: 'tenants.modal-button-cancel' })}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}

interface ITenantModalProps {
  stateModal: TStateModal;
  createTenant(name: string): void;
  changeNameTenant(tenant: TChangeTenantNamePayload): void;
  closeModal(): void;
}

export type TStateModal = IStateCreateModal | TStateEditModal;

export interface IStateCreateModal {
  isOpen: boolean;
  type: ETypeTenantModal;
}

export type TStateEditModal = IStateCreateModal & Pick<ITenant, 'id' | 'tenantName'>;

export interface IDataTenantModal {
  title: string;
  description: string;
  footnote?: string;
  button: string;
  action: (e: React.FormEvent<HTMLFormElement>) => void;
}
