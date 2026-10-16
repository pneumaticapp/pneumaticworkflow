import * as React from 'react';
import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { Formik } from 'formik';
import type { FormikProps } from 'formik';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { Button } from '../../../UI/Buttons/Button';
import { NotificationManager } from '../../../UI/Notifications';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { FormikTextareaField } from '../../../UI/Fields/TextareaField';
import { ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { validateRequired } from '../../../../utils/validators';
import { uploadUserAvatar } from '../../../../utils/uploadFiles';
import { getAIProviderModelsState, getAIProviders } from '../../../../redux/selectors/ai';
import { EMPTY_AI_AGENT_FORM_VALUES } from './types';
import type { IAIAgentFormProps, IAIAgentFormValues } from './types';
import { ProviderModelsSync } from './ProviderModelsSync';
import { getAgentInitials } from '../getAgentInitials';

import styles from './CreatePerformerModal.css';

export function CreateAIAgentForm({
  isActive,
  isOpen,
  isSubmitting = false,
  initialValues = EMPTY_AI_AGENT_FORM_VALUES,
  submitLabel,
  onSubmit,
}: IAIAgentFormProps) {
  const { formatMessage } = useIntl();
  const latestAvatarActionRef = useRef(0);
  const [isAvatarUploading, setIsAvatarUploading] = useState(false);
  const providers = useSelector(getAIProviders);
  const modelsState = useSelector(getAIProviderModelsState);
  const formikRef = useRef<FormikProps<IAIAgentFormValues> | null>(null);
  const wasOpenRef = useRef(isOpen);

  useEffect(() => {
    if (isOpen && !wasOpenRef.current) {
      latestAvatarActionRef.current += 1;
      setIsAvatarUploading(false);
      formikRef.current?.resetForm();
    }
    wasOpenRef.current = isOpen;
  }, [isOpen]);

  const providerOptions = providers.map((provider) => ({
    label: `${provider.name} — ${provider.apiKeyPrefix}`,
    value: String(provider.id),
  }));

  return (
    <Formik
      innerRef={formikRef}
      initialValues={initialValues}
      validateOnMount
      validate={(values) => {
        const providerError = validateRequired(values.providerId);
        const modelError = validateRequired(values.model);

        return {
          ...(validateRequired(values.name) && { name: validateRequired(values.name) }),
          ...(providerError && { providerId: formatMessage({ id: providerError }) }),
          ...(modelError && { model: formatMessage({ id: modelError }) }),
          ...(validateRequired(values.systemPrompt) && { systemPrompt: validateRequired(values.systemPrompt) }),
        };
      }}
      onSubmit={onSubmit}
    >
      {({ dirty, handleSubmit, isValid, setFieldValue, values }) => {
        const initials = getAgentInitials(values.name);

        const handleAvatarUpload = async (event: ChangeEvent<HTMLInputElement>) => {
          const file = event.target.files?.[0];
          if (!file) return;

          latestAvatarActionRef.current += 1;
          const actionId = latestAvatarActionRef.current;
          event.currentTarget.value = '';

          setIsAvatarUploading(true);
          try {
            const [uploaded] = await uploadUserAvatar(file);
            if (actionId === latestAvatarActionRef.current && uploaded && !uploaded.error) {
              await setFieldValue('photo', uploaded.url);
            }
          } catch {
            if (actionId === latestAvatarActionRef.current) {
              NotificationManager.warning({ message: 'file-service.upload-failed' });
            }
          } finally {
            if (actionId === latestAvatarActionRef.current) {
              setIsAvatarUploading(false);
            }
          }
        };

        const isModelSelectDisabled = !values.providerId || modelsState.isLoading;
        const modelOptions =
          modelsState.providerId === Number(values.providerId)
            ? modelsState.list.map((model) => ({ label: model.name, value: model.slug }))
            : [];
        const modelPlaceholder = (() => {
          if (!values.providerId) return formatMessage({ id: 'team.create-ai-agent-modal.model-select-provider' });
          if (modelsState.isLoading) return formatMessage({ id: 'team.create-ai-agent-modal.model-loading' });
          return undefined;
        })();

        if (!isActive) return null;

        return (
          <form onSubmit={handleSubmit}>
            <ProviderModelsSync />
            <ModalBody className={styles['modal__body']}>
              <div className={styles['modal__agent-avatar']}>
                <div className={styles['modal__avatar-preview']}>
                  {values.photo ? <img src={values.photo} alt="" /> : initials}
                </div>
                <div className={styles['modal__avatar-actions']}>
                  <label htmlFor="ai-agent-avatar-upload">
                    {formatMessage({ id: 'team.create-ai-agent-modal.upload' })}
                    <input id="ai-agent-avatar-upload" type="file" accept="image/*" onChange={handleAvatarUpload} />
                  </label>
                  <span className={styles['modal__avatar-separator']} aria-hidden>
                    •
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      latestAvatarActionRef.current += 1;
                      setIsAvatarUploading(false);
                      setFieldValue('photo', '');
                    }}
                  >
                    {formatMessage({ id: 'team.create-ai-agent-modal.generate' })}
                  </button>
                </div>
              </div>

              <div className={styles['modal__form']}>
                <FormikInputField
                  name="name"
                  title={formatMessage({ id: 'team.create-ai-agent-modal.name' })}
                  isRequired
                  fieldSize="lg"
                />
                <h3 className={styles['modal__section-title']}>
                  {formatMessage({ id: 'team.create-ai-agent-modal.parameters' })}
                </h3>
                <FormikDropdownList
                  name="providerId"
                  label={formatMessage({ id: 'team.create-ai-agent-modal.provider' })}
                  options={providerOptions}
                  isRequired
                />
                <FormikDropdownList
                  name="model"
                  label={formatMessage({ id: 'team.create-ai-agent-modal.model' })}
                  options={modelOptions}
                  isRequired
                  isSearchable
                  isDisabled={isModelSelectDisabled}
                  placeholder={modelPlaceholder}
                  filterOption={(option: { label: string; value: string }, input: string) =>
                    `${option.label} ${option.value}`.toLowerCase().includes(input.toLowerCase())
                  }
                />
                <FormikTextareaField
                  name="systemPrompt"
                  title={formatMessage({ id: 'team.create-ai-agent-modal.system-prompt' })}
                  isRequired
                  rows={5}
                />
              </div>
            </ModalBody>
            <ModalFooter className={styles['modal__footer']}>
              <Button
                className={styles['modal__submit']}
                type="submit"
                label={submitLabel}
                buttonStyle="yellow"
                disabled={!dirty || !isValid || isSubmitting || isAvatarUploading}
                isLoading={isSubmitting}
              />
            </ModalFooter>
          </form>
        );
      }}
    </Formik>
  );
}
