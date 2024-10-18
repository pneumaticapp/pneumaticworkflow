import React, { useState } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { TStateEditModal } from '../TenantModal';
import { WarningPopup } from '../../UI/WarningPopup';
import { Dropdown, Header, TDropdownOption } from '../../UI';
import { DateFormat } from '../../UI/DateFormat';
import { TLoginPartnerSuperuserPayload } from '../../../redux/actions';
import { MoreIcon, PencilIcon, TenantIcon, TrashIcon } from '../../icons';

import styles from './Tenant.css';

export function Tenant({ id, name, dateJoined, loginPartnerSuperuser, deleteTenant, openModalEdit }: ITenantProps) {
  const { formatMessage } = useIntl();

  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

  const openDeleteTemplateModal = () => {
    setIsDeleteModalVisible(true);
  };

  const closeDeleteTemplateModal = () => {
    setIsDeleteModalVisible(false);
  };

  const handleDeleteTenant = () => {
    deleteTenant(id);
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'tenants.dropdown-edit-name' }),
      onClick: () => {
        openModalEdit({ id, tenantName: name });
      },
      Icon: PencilIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'tenants.dropdown-delete' }),
      onClick: openDeleteTemplateModal,
      Icon: TrashIcon,
      color: 'red',
      withUpperline: true,
      size: 'sm',
    },
  ];

  return (
    <section className={styles['tenant']}>
      <WarningPopup
        isOpen={isDeleteModalVisible}
        closeModal={closeDeleteTemplateModal}
        title={formatMessage({ id: 'tenants.delete-title' })}
        message={formatMessage({ id: 'tenants.delete-message' }, { name: <b key={name}>{name}</b> })}
        acceptTitle={formatMessage({ id: 'tenants.delete-accept' })}
        declineTitle={formatMessage({ id: 'tenants.delete-decline' })}
        onConfirm={() => handleDeleteTenant()}
        onReject={closeDeleteTemplateModal}
      />
      <div className={styles['tenant__icon']}>
        <TenantIcon />
      </div>
      <div className={styles['tenant__user']}>
        <Header
          size="6"
          tag="h2"
          className={styles['tenant__name']}
          onClick={() => loginPartnerSuperuser({ tenantId: id })}
        >
          {name}
        </Header>
        <p className={styles['tenant__date']}>
          {formatMessage({ id: 'tenants.date-started' }, { date: <DateFormat date={dateJoined} /> })}
        </p>
      </div>
      <div className={styles['tenant__info']}>
        <Dropdown
          className={styles['tenant__dropdown']}
          renderToggle={(isOpen) => (
            <MoreIcon className={classnames(styles['tenant__more'], isOpen && styles['is-active'])} />
          )}
          options={dropdownOptions}
        />
      </div>
    </section>
  );
}

interface ITenantProps {
  id: number;
  name: string;
  dateJoined: string;
  loginPartnerSuperuser(payload: TLoginPartnerSuperuserPayload): void;
  openModalEdit(tenant: Pick<TStateEditModal, 'id' | 'tenantName'>): void;
  deleteTenant(id: number): void;
}
