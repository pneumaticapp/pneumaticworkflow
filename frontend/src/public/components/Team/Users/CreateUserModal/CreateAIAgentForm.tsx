import React, { useEffect, useRef } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { Button } from '../../../UI/Buttons/Button';
import { FormikDropdownList } from '../../../UI/DropdownList';
import { FormikInputField } from '../../../UI/Fields/InputField';
import { ModalBody, ModalFooter } from '../../../UI/BaseModal';
import { isEmpty } from '../../../../utils/validators';
import { uploadUserAvatar } from '../../../../utils/uploadFiles';
import { loadAIProviderModels } from '../../../../redux/ai/slice';
import { getAIProviderModelsState, getAIProviders } from '../../../../redux/selectors/ai';
import { IAIAgentFormProps, IAIAgentFormValues } from './types';

import styles from './CreateUserModal.css';

const REQUIRED_ERROR = 'team.create-ai-agent-modal.validation-required';
const validateRequired = (value: string) => (isEmpty(value) ? REQUIRED_ERROR : '');

export const EMPTY_AI_AGENT_FORM_VALUES: IAIAgentFormValues = {
  name: '',
  providerId: '',
  model: '',
  systemPrompt: '',
  photo: '',
};

function ResetFormOnReopen({
  isOpen,
  latestAvatarActionRef,
}: {
  isOpen: boolean;
  latestAvatarActionRef: React.MutableRefObject<number>;
}) {
  const { resetForm } = useFormikContext<IAIAgentFormValues>();
  const wasOpenRef = useRef(isOpen);

  useEffect(() => {
    if (isOpen && !wasOpenRef.current) {
      latestAvatarActionRef.current += 1;
      resetForm();
    }
    wasOpenRef.current = isOpen;
  }, [isOpen, latestAvatarActionRef, resetForm]);

  return null;
}

/**
 * Keeps the model list in sync with the picked provider: loads models when a provider is
 * selected, clears the picked model when the provider changes (a slug belongs to one provider),
 * and preselects the provider when the account has exactly one.
 */
function ProviderModelsSync({ initialProviderId }: { initialProviderId: string }) {
  const dispatch = useDispatch();
  const providers = useSelector(getAIProviders);
  const { values, setFieldValue } = useFormikContext<IAIAgentFormValues>();
  const prevProviderIdRef = useRef(initialProviderId);

  useEffect(() => {
    if (!values.providerId && providers.length === 1) {
      setFieldValue('providerId', String(providers[0].id));
    }
  }, [values.providerId, providers, setFieldValue]);

  useEffect(() => {
    if (!values.providerId) {
      return;
    }

    if (values.providerId !== prevProviderIdRef.current && values.model) {
      setFieldValue('model', '');
    }
    prevProviderIdRef.current = values.providerId;

    dispatch(loadAIProviderModels(Number(values.providerId)));
  }, [values.providerId, dispatch, setFieldValue]);

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

export function CreateAIAgentForm({
  isActive,
  isOpen,
  initialValues = EMPTY_AI_AGENT_FORM_VALUES,
  submitLabel,
  onSubmit,
}: IAIAgentFormProps) {
  const { formatMessage } = useIntl();
  const latestAvatarActionRef = useRef(0);
  const providers = useSelector(getAIProviders);
  const modelsState = useSelector(getAIProviderModelsState);

  const providerOptions = providers.map((provider) => ({
    label: `${provider.name} — ${provider.baseUrl}`,
    value: String(provider.id),
  }));

  return (
    <Formik
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
        const initials = values.name
          .split(' ')
          .filter(Boolean)
          .slice(0, 2)
          .map((word) => word.charAt(0))
          .join('')
          .toUpperCase();

        const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
          const file = event.target.files?.[0];
          if (!file) return;

          latestAvatarActionRef.current += 1;
          const actionId = latestAvatarActionRef.current;
          event.currentTarget.value = '';

          // The API stores a hosted URL, so the file goes to the file service right away.
          const [uploaded] = await uploadUserAvatar(file);
          if (actionId === latestAvatarActionRef.current && uploaded && !uploaded.error) {
            setFieldValue('photo', uploaded.url);
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

        const resetFormOnReopen = (
          <ResetFormOnReopen
            isOpen={isOpen}
            latestAvatarActionRef={latestAvatarActionRef}
          />
        );

        if (!isActive) return resetFormOnReopen;

        return (
          <form onSubmit={handleSubmit}>
            {resetFormOnReopen}
            <ProviderModelsSync initialProviderId={initialValues.providerId} />
            <ModalBody className={styles['modal__body']}>
              <div className={styles['modal__agent-avatar']}>
                <div className={styles['modal__avatar-preview']}>
                  {values.photo ? <img src={values.photo} alt="" /> : initials}
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
                <SystemPromptField />
              </div>
            </ModalBody>
            <ModalFooter className={styles['modal__footer']}>
              <Button
                className={styles['modal__submit']}
                type="submit"
                label={submitLabel}
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
