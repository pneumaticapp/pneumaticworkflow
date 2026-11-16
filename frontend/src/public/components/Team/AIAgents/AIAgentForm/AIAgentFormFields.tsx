import React, { useState, type ChangeEvent } from 'react';
import { useFormikContext } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../../../UI/Buttons/Button';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { FormikTextareaField } from '../../../UI/Fields/TextareaField';
import { ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { uploadAIAgentAvatar } from '../../../../redux/ai/slice';
import {
  getAIProviderModelsIsLoading,
  getAIProviderModelsList,
  getAIProviderModelsProviderId,
  getAIProvidersList,
} from '../../../../redux/selectors/ai';
import { AgentAvatar } from '../AgentAvatar';
import { generateAgentAvatar } from '../utils/generateAgentAvatar';
import type { IAIAgentFormFieldsProps, IAIAgentFormValues } from './types';
import { useProviderModelsSync } from './useProviderModelsSync';

import modalStyles from '../../PerformerModal.css';
import styles from './AIAgentForm.css';

const filterModelOption = (option: { label: string; value: string }, input: string) =>
  `${option.label} ${option.value}`.toLowerCase().includes(input.toLowerCase());

export function AIAgentFormFields({ isSubmitting, submitLabel }: IAIAgentFormFieldsProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const providers = useSelector(getAIProvidersList);
  const models = useSelector(getAIProviderModelsList);
  const isModelsLoading = useSelector(getAIProviderModelsIsLoading);
  const modelsProviderId = useSelector(getAIProviderModelsProviderId);
  const { dirty, handleSubmit, isValid, setFieldValue, values } = useFormikContext<IAIAgentFormValues>();
  const [isAvatarUploading, setIsAvatarUploading] = useState(false);
  useProviderModelsSync();

  const providerOptions = providers.map((provider) => ({
    label: `${provider.name} — ${provider.apiKeyPrefix}`,
    value: String(provider.id),
  }));

  const handleAvatarUploaded = (url: string) => {
    setFieldValue('photo', url);
  };

  const handleAvatarUploadSettled = () => {
    setIsAvatarUploading(false);
  };

  const uploadAvatar = (file: File) => {
    setIsAvatarUploading(true);
    dispatch(uploadAIAgentAvatar({ file, onSuccess: handleAvatarUploaded, onSettled: handleAvatarUploadSettled }));
  };

  const handleAvatarUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    event.currentTarget.value = '';
    uploadAvatar(file);
  };

  const handleAvatarGenerate = async () => {
    const file = await generateAgentAvatar();
    if (file) uploadAvatar(file);
  };

  const isModelSelectDisabled = !values.providerId || isModelsLoading;
  const modelOptions =
    modelsProviderId === Number(values.providerId)
      ? models.map((model) => ({ label: model.name, value: model.slug }))
      : [];
  const modelPlaceholder = (() => {
    if (!values.providerId) return formatMessage({ id: 'team.create-ai-agent-modal.model-select-provider' });
    if (isModelsLoading) return formatMessage({ id: 'team.create-ai-agent-modal.model-loading' });
    return undefined;
  })();

  return (
    <form onSubmit={handleSubmit}>
      <ModalBody className={modalStyles['performer-modal__body']}>
        <div className={styles['ai-agent-form__avatar']}>
          <AgentAvatar name={values.name} photo={values.photo} size="lg" />
          <div className={styles['ai-agent-form__avatar-actions']}>
            <label htmlFor="ai-agent-avatar-upload">
              {formatMessage({ id: 'team.create-ai-agent-modal.upload' })}
              <input id="ai-agent-avatar-upload" type="file" accept="image/*" onChange={handleAvatarUpload} />
            </label>
            <span className={styles['ai-agent-form__avatar-separator']} aria-hidden>
              •
            </span>
            <button type="button" onClick={handleAvatarGenerate}>
              {formatMessage({ id: 'team.create-ai-agent-modal.generate' })}
            </button>
          </div>
        </div>

        <div className={modalStyles['performer-modal__form']}>
          <FormikInputField
            name="name"
            title={formatMessage({ id: 'team.create-ai-agent-modal.name' })}
            isRequired
            fieldSize="lg"
          />
          <h3 className={styles['ai-agent-form__section-title']}>
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
            filterOption={filterModelOption}
          />
          <FormikTextareaField
            name="systemPrompt"
            title={formatMessage({ id: 'team.create-ai-agent-modal.system-prompt' })}
            isRequired
            className={styles['ai-agent-form__prompt']}
          />
        </div>
      </ModalBody>
      <ModalFooter className={modalStyles['performer-modal__footer']}>
        <Button
          className={modalStyles['performer-modal__submit']}
          type="submit"
          label={submitLabel}
          buttonStyle="yellow"
          disabled={!dirty || !isValid || isSubmitting || isAvatarUploading}
          isLoading={isSubmitting}
        />
      </ModalFooter>
    </form>
  );
}
