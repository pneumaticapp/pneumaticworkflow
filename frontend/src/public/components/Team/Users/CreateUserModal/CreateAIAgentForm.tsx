import React, { useEffect, useRef } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { useIntl } from 'react-intl';

import { Button } from '../../../UI/Buttons/Button';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { isEmpty, isInvalidUrlWithProtocol, validateName } from '../../../../utils/validators';
import { ICreateAIAgentFormProps, ICreateAIAgentFormValues } from './types';

import styles from './CreateUserModal.css';

const MODEL_OPTIONS = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google Gemini', value: 'gemini' },
];

const REQUIRED_ERROR = 'team.create-ai-agent-modal.validation-required';
const validateRequired = (value: string) => (isEmpty(value) ? REQUIRED_ERROR : '');
const validateEndpoint = (value: string) => (
  validateRequired(value)
  || (isInvalidUrlWithProtocol(value) ? 'validation.url-invalid' : '')
);

function ResetFormOnReopen({ isOpen }: { isOpen: boolean }) {
  const { resetForm } = useFormikContext<ICreateAIAgentFormValues>();
  const wasOpenRef = useRef(isOpen);

  useEffect(() => {
    if (isOpen && !wasOpenRef.current) resetForm();
    wasOpenRef.current = isOpen;
  }, [isOpen, resetForm]);

  return null;
}

function SystemPromptField() {
  const { formatMessage } = useIntl();
  const [field, meta] = useField<string>('systemPrompt');

  return (
    <label className={styles['modal__textarea-field']} htmlFor="ai-agent-system-prompt">
      <span>{formatMessage({ id: 'team.create-ai-agent-modal.system-prompt' })}</span>
      <textarea {...field} id="ai-agent-system-prompt" rows={5} />
      {meta.touched && meta.error && (
        <span className={styles['modal__error']}>{formatMessage({ id: meta.error })}</span>
      )}
    </label>
  );
}

export function CreateAIAgentForm({ isActive, isOpen, onSubmit }: ICreateAIAgentFormProps) {
  const { formatMessage } = useIntl();
  const latestAvatarActionRef = useRef(0);
  const initialValues: ICreateAIAgentFormValues = {
    firstName: '',
    lastName: '',
    position: '',
    model: '',
    endpoint: '',
    apiKey: '',
    systemPrompt: '',
    avatar: '',
  };

  return (
    <Formik
      initialValues={initialValues}
      validateOnMount
      validate={(values) => {
        const modelError = validateRequired(values.model);

        return {
          ...(validateName(values.firstName) && { firstName: validateName(values.firstName) }),
          ...(validateName(values.lastName) && { lastName: validateName(values.lastName) }),
          ...(validateRequired(values.position) && { position: validateRequired(values.position) }),
          ...(modelError && { model: formatMessage({ id: modelError }) }),
          ...(validateEndpoint(values.endpoint) && { endpoint: validateEndpoint(values.endpoint) }),
          ...(validateRequired(values.apiKey) && { apiKey: validateRequired(values.apiKey) }),
        };
      }}
      onSubmit={onSubmit}
    >
      {({ dirty, handleSubmit, isValid, setFieldValue, values }) => {
        const initials = `${values.firstName.charAt(0)}${values.lastName.charAt(0)}`.toUpperCase();
        const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
          const file = event.target.files?.[0];
          if (!file) return;

          latestAvatarActionRef.current += 1;
          const actionId = latestAvatarActionRef.current;
          const reader = new FileReader();
          reader.onload = () => {
            if (actionId === latestAvatarActionRef.current) {
              setFieldValue('avatar', String(reader.result));
            }
          };
          reader.readAsDataURL(file);
          event.currentTarget.value = '';
        };

        if (!isActive) return <ResetFormOnReopen isOpen={isOpen} />;

        return (
          <form onSubmit={handleSubmit}>
            <ResetFormOnReopen isOpen={isOpen} />
            <ModalBody className={styles['modal__body']}>
              <div className={styles['modal__agent-avatar']}>
                <div className={styles['modal__avatar-preview']}>
                  {values.avatar.startsWith('data:')
                    ? <img src={values.avatar} alt="" />
                    : values.avatar === 'generated' && initials}
                </div>
                <div className={styles['modal__avatar-actions']}>
                  <label htmlFor="ai-agent-avatar-upload">
                    {formatMessage({ id: 'team.create-ai-agent-modal.upload' })}
                    <input
                      id="ai-agent-avatar-upload"
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                    />
                  </label>
                  <span className={styles['modal__avatar-separator']} aria-hidden>•</span>
                  <button
                    type="button"
                    onClick={() => {
                      latestAvatarActionRef.current += 1;
                      setFieldValue('avatar', 'generated');
                    }}
                  >
                    {formatMessage({ id: 'team.create-ai-agent-modal.generate' })}
                  </button>
                </div>
              </div>

              <div className={styles['modal__form']}>
                <FormikInputField
                  name="firstName"
                  title={formatMessage({ id: 'team.create-user-modal.first-name' })}
                  isRequired
                  fieldSize="lg"
                />
                <FormikInputField
                  name="lastName"
                  title={formatMessage({ id: 'team.create-user-modal.last-name' })}
                  isRequired
                  fieldSize="lg"
                />
                <FormikInputField
                  name="position"
                  title={formatMessage({ id: 'team.create-ai-agent-modal.position' })}
                  isRequired
                  fieldSize="lg"
                />
                <h3 className={styles['modal__section-title']}>
                  {formatMessage({ id: 'team.create-ai-agent-modal.parameters' })}
                </h3>
                <FormikDropdownList
                  name="model"
                  label={formatMessage({ id: 'team.create-ai-agent-modal.model' })}
                  options={MODEL_OPTIONS}
                  isRequired
                />
                <FormikInputField
                  name="endpoint"
                  title={formatMessage({ id: 'team.create-ai-agent-modal.endpoint' })}
                  isRequired
                  fieldSize="lg"
                />
                <FormikInputField
                  name="apiKey"
                  title={formatMessage({ id: 'team.create-ai-agent-modal.api-key' })}
                  isRequired
                  fieldSize="lg"
                  type="password"
                  showPasswordVisibilityToggle
                />
                <SystemPromptField />
              </div>
            </ModalBody>
            <ModalFooter className={styles['modal__footer']}>
              <Button
                className={styles['modal__submit']}
                type="submit"
                label={formatMessage({ id: 'team.create-ai-agent-modal.submit' })}
                buttonStyle="yellow"
                disabled={!dirty || !isValid}
              />
            </ModalFooter>
          </form>
        );
      }}
    </Formik>
  );
}
