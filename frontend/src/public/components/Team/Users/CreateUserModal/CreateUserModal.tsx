import * as React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { BaseModal, ModalHeader, ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { Button } from '../../../UI/Buttons/Button';
import { Tabs } from '../../../UI/Tabs';
import { validateEmail, validateRegistrationPassword } from '../../../../utils/validators';
import { getErrorsObject } from '../../../../utils/formik/getErrorsObject';
import { copyToClipboard } from '../../../../utils/helpers';
import { createPassword } from '../../../../utils/createPassword';
import { NotificationManager } from '../../../UI/Notifications';
import { createUser } from '../../../../redux/accounts/slice';

import { CreateAIAgentForm } from './CreateAIAgentForm';
import {
  ECreateUserModalTab,
  EUserRole,
  ICreateUserFormValues,
  ICreateUserModalProps,
  IStatusOption,
} from './types';

import styles from './CreateUserModal.css';

const formatStatusOption = (
  { label, value }: IStatusOption,
  { context }: { context: string },
  selectedValue: IStatusOption['value'],
) => {
  if (context === 'menu' && value === selectedValue) {
    return <span className={styles['modal__option--selected']}>{label}</span>;
  }
  return label;
};

export function CreateUserModal({ isOpen, onClose, onCreateAIAgent }: ICreateUserModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const [activeTab, setActiveTab] = useState(ECreateUserModalTab.User);

  useEffect(() => {
    if (isOpen) setActiveTab(ECreateUserModalTab.User);
  }, [isOpen]);

  const statusOptions: IStatusOption[] = [
    { label: formatMessage({ id: 'team.create-user-modal.status-admin' }), value: EUserRole.Admin },
    { label: formatMessage({ id: 'team.create-user-modal.status-user' }), value: EUserRole.User },
  ];

  const initialValues: ICreateUserFormValues = useMemo(
    () => ({
      firstName: '',
      lastName: '',
      email: '',
      role: EUserRole.User,
      password: createPassword(),
    }),
    [isOpen],
  );

  const handleSubmit = (values: ICreateUserFormValues) => {
    const { role, ...userData } = values;
    dispatch(createUser({ ...userData, isAdmin: role === EUserRole.Admin }));
  };

  return (
    <BaseModal
      isOpen={isOpen}
      toggle={onClose}
      className={
        activeTab === ECreateUserModalTab.AIAgent
          ? `${styles['modal__dialog']} ${styles['modal__dialog--ai-agent']}`
          : styles['modal__dialog']
      }
      contentClassName={
        activeTab === ECreateUserModalTab.AIAgent
          ? `${styles['modal__content']} ${styles['modal__content--ai-agent']}`
          : styles['modal__content']
      }
    >
      <ModalHeader
        toggle={onClose}
        className={styles['modal__header']}
        titleTag="div"
      >
        <div data-testid="create-user-modal-header" className={styles['modal__tabs']}>
          <Tabs
            values={[
              { id: ECreateUserModalTab.User, label: formatMessage({ id: 'team.create-user-modal.tab-user' }) },
              { id: ECreateUserModalTab.AIAgent, label: formatMessage({ id: 'team.create-user-modal.tab-ai-agent' }) },
            ]}
            activeValueId={activeTab}
            containerClassName={styles['modal__tabs-switcher']}
            tabClassName={styles['modal__tab']}
            activeTabClassName={styles['modal__tab_active']}
            onChange={setActiveTab}
          />
        </div>
      </ModalHeader>

      <CreateAIAgentForm
        isActive={activeTab === ECreateUserModalTab.AIAgent}
        isOpen={isOpen}
        onSubmit={(values) => onCreateAIAgent?.(values)}
      />
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validate={(values) => {
          const errors = getErrorsObject(values, {
            email: validateEmail,
            password: validateRegistrationPassword,
          });

          return errors;
        }}
      >
        {({ values, handleSubmit: formikSubmit, isValid, dirty }) => {
          if (activeTab !== ECreateUserModalTab.User) return null;

          const currentStatusValue = values.role;
          const renderStatusOption = (option: IStatusOption, { context }: { context: string }) =>
            formatStatusOption(option, { context }, currentStatusValue);

          return (
            <form onSubmit={formikSubmit}>
              <ModalBody className={styles['modal__body']}>
                <div className={styles['modal__form']}>
                  <FormikInputField
                    name="firstName"
                    title={formatMessage({ id: 'team.create-user-modal.first-name' })}
                    fieldSize="lg"
                    containerClassName={styles['modal__input-ellipsis']}
                  />
                  <FormikInputField
                    name="lastName"
                    title={formatMessage({ id: 'team.create-user-modal.last-name' })}
                    fieldSize="lg"
                    containerClassName={styles['modal__input-ellipsis']}
                  />
                  <FormikInputField
                    name="email"
                    title={formatMessage({ id: 'team.create-user-modal.email' })}
                    fieldSize="lg"
                    isRequired
                    type="email"
                    containerClassName={styles['modal__input-ellipsis']}
                  />

                  <FormikDropdownList
                    name="role"
                    label={formatMessage({ id: 'team.create-user-modal.status' })}
                    options={statusOptions}
                    isRequired
                    formatOptionLabel={renderStatusOption}
                  />

                  <div className={styles['modal__password-field']}>
                    <FormikInputField
                      name="password"
                      title={formatMessage({ id: 'team.create-user-modal.password' })}
                      fieldSize="lg"
                      type="text"
                      isRequired
                      containerClassName={`${styles['modal__input-ellipsis']} ${styles['modal__password-input-wrap']}`}
                    />
                    <button
                      type="button"
                      className={styles['modal__copy-btn']}
                      onClick={() => {
                        copyToClipboard(values.password || '');
                        NotificationManager.success({ message: 'team.create-user-modal.password-copied' });
                      }}
                    >
                      {formatMessage({ id: 'team.create-user-modal.copy' })}
                    </button>
                  </div>
                </div>
              </ModalBody>

              <ModalFooter className={styles['modal__footer']}>
                <Button
                  className={styles['modal__submit']}
                  type="submit"
                  label={formatMessage({ id: 'team.create-user-modal.submit' })}
                  buttonStyle="yellow"
                  disabled={!isValid || !dirty}
                />
              </ModalFooter>
            </form>
          );
        }}
      </Formik>
    </BaseModal>
  );
}
