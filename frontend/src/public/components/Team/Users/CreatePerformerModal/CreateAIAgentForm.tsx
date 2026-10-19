import * as React from 'react';
import type { ChangeEvent } from 'react';
import { Formik } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../../../UI/Buttons/Button';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { FormikTextareaField } from '../../../UI/Fields/TextareaField';
import { ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { getErrorsObject } from '../../../../utils/formik/getErrorsObject';
import { validateRequired } from '../../../../utils/validators';
import { cancelAIAgentAvatarUpload, uploadAIAgentAvatar } from '../../../../redux/ai/slice';
import { getAIAgentAvatarUploadState, getAIProviderModelsState, getAIProviders } from '../../../../redux/selectors/ai';
import { EMPTY_AI_AGENT_FORM_VALUES } from './constants';
import type { IAIAgentFormProps } from './types';
import { ProviderModelsSync } from './ProviderModelsSync';
import { getAgentInitials } from '../getAgentInitials';

import styles from './CreatePerformerModal.css';

export function CreateAIAgentForm({
  isActive,
  isSubmitting = false,
  initialValues = EMPTY_AI_AGENT_FORM_VALUES,
  submitLabel,
  onSubmit,
}: IAIAgentFormProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { isLoading: isAvatarUploading } = useSelector(getAIAgentAvatarUploadState);
  const providers = useSelector(getAIProviders);
  const modelsState = useSelector(getAIProviderModelsState);
  const providerOptions = providers.map((provider) => ({
    label: `${provider.name} — ${provider.apiKeyPrefix}`,
    value: String(provider.id),
  }));

  return (
    <Formik
      initialValues={initialValues}
      validateOnMount
      validate={(values) =>
        getErrorsObject(values, {
          name: validateRequired,
          providerId: validateRequired,
          model: validateRequired,
          systemPrompt: validateRequired,
        })
      }
      onSubmit={onSubmit}
    >
      {({ dirty, handleSubmit, isValid, setFieldValue, values }) => {
        const initials = getAgentInitials(values.name);

        const handleAvatarUpload = (event: ChangeEvent<HTMLInputElement>) => {
          const file = event.target.files?.[0];
          if (!file) return;

          event.currentTarget.value = '';
          dispatch(uploadAIAgentAvatar({ file, onSuccess: (url) => setFieldValue('photo', url) }));
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
                      dispatch(cancelAIAgentAvatarUpload());
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
