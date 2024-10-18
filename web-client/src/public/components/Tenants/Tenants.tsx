import React, { useEffect, useState } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { AddTenantIcon } from '../icons/AddTenantIcon';
import { TITLES } from '../../constants/titles';
import { TChangeTenantNamePayload, TLoginPartnerSuperuserPayload } from '../../redux/actions';
import { TenantsSkeleton } from './TenantSkeleton/TenantsSkeleton';
import { TStateEditModal, TStateModal, TenantModal } from './TenantModal';
import { ETenantsSorting, ETypeTenantModal, ITenant } from '../../types/tenants';
import { Tenant } from './Tenant/Tenant';
import { TenantGuestBanner } from './TenantGuestBanner';

import styles from './Tenants.css';

export function Tenants({
  tenants,
  isLoading,
  loadTenants,
  loginPartnerSuperuser,
  createTenant,
  changeTenantName,
  deleteTenant,
}: ITenantsProps) {
  const { formatMessage } = useIntl();

  const [stateModal, setStateModal] = useState<TStateModal>({
    isOpen: false,
    type: ETypeTenantModal.Create,
    id: -1,
    tenantName: '',
  });

  useEffect(() => {
    document.title = TITLES.Tenants;
    loadTenants();
  }, []);

  const handleOpenModalCreate = () => {
    setStateModal({
      isOpen: true,
      type: ETypeTenantModal.Create,
    });
  };

  const handleOpenModalEdit = ({ id, tenantName }: Pick<TStateEditModal, 'id' | 'tenantName'>) => {
    setStateModal({
      isOpen: true,
      type: ETypeTenantModal.EditName,
      id,
      tenantName,
    });
  };

  const handleCloseModal = () => {
    setStateModal({
      isOpen: false,
      type: ETypeTenantModal.Create,
    });
  };

  const renderAddTenant = () => {
    return (
      <button type="button" className={styles['tenants-add']} onClick={() => handleOpenModalCreate()}>
        <div className={styles['tenants-add__icon']}>
          <AddTenantIcon />
        </div>
        <div>
          <h2>{formatMessage({ id: 'tenants.add-title' })}</h2>
          <p>{formatMessage({ id: 'tenants.add-caption' })}</p>
        </div>
      </button>
    );
  };

  const renderTenants = () => {
    if (isLoading) {
      return new Array(3).fill(1).map((index, item) => {
        return (
          <div key={index + item.toString()} className={styles['tenants__item']}>
            <TenantsSkeleton />
          </div>
        );
      });
    }

    return tenants.map((tenant) => {
      return (
        <article key={tenant.dateJoined} className={styles['tenants__item']}>
          <Tenant
            id={tenant.id}
            name={tenant.tenantName}
            dateJoined={tenant.dateJoined}
            loginPartnerSuperuser={loginPartnerSuperuser}
            deleteTenant={deleteTenant}
            openModalEdit={handleOpenModalEdit}
          />
        </article>
      );
    });
  };

  return (
    <div>
      <div className={classnames(styles['container'], { [styles['container-loading']]: isLoading })}>
        {isLoading && <div className="loading" />}

        <TenantGuestBanner />
        {renderAddTenant()}
        {renderTenants()}
      </div>
      <TenantModal
        stateModal={stateModal}
        createTenant={createTenant}
        changeNameTenant={changeTenantName}
        closeModal={handleCloseModal}
      />
    </div>
  );
}

export interface ITenantsProps {
  sorting: ETenantsSorting;
  isLoading: boolean;
  tenants: ITenant[];
  loadTenants(): void;
  loginPartnerSuperuser(payload: TLoginPartnerSuperuserPayload): void;
  createTenant(name: string): void;
  changeTenantName(tenant: TChangeTenantNamePayload): void;
  deleteTenant(id: number): void;
}
