import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { closeAiAgentModal, createAiAgent, loadAiModels, updateAiAgent } from '../../../redux/actions';
import { getAiAgentsEditModal, getAiModelsState } from '../../../redux/selectors/aiAgents';
import { Button, Header, InputField, Modal } from '../../UI';
import { DropdownList } from '../../UI/DropdownList';

import styles from './AiAgentModal.css';

const MAX_TEMPERATURE = 2;

export function AiAgentModal() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const { isOpen, editAgent } = useSelector(getAiAgentsEditModal);
  const { list: models } = useSelector(getAiModelsState);

  const [name, setName] = useState('');
  const [modelSlug, setModelSlug] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [temperature, setTemperature] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && !models.length) {
      dispatch(loadAiModels());
    }
  }, [isOpen]);

  useEffect(() => {
    setName(editAgent?.name || '');
    setModelSlug(editAgent?.modelSlug || '');
    setSystemPrompt(editAgent?.systemPrompt || '');
    setTemperature(editAgent?.temperature != null ? String(editAgent.temperature) : '');
    setError('');
  }, [editAgent, isOpen]);

  const modelOptions = useMemo(() => {
    const options = models.map((model) => ({
      label: `${model.name} — ${model.slug}`,
      value: model.slug,
    }));
    // an agent may keep a model missing from the current catalog
    // (retired or from another provider) — keep it selectable
    if (modelSlug && !models.some((model) => model.slug === modelSlug)) {
      options.unshift({ label: modelSlug, value: modelSlug });
    }
    return options;
  }, [models, modelSlug]);

  const parseTemperature = (): number | null | undefined => {
    if (!temperature.trim()) return null;

    const value = Number(temperature);
    if (Number.isNaN(value) || value < 0 || value > MAX_TEMPERATURE) {
      return undefined;
    }

    return value;
  };

  const handleCloseModal = () => {
    dispatch(closeAiAgentModal());
    setError('');
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const parsedTemperature = parseTemperature();
    if (parsedTemperature === undefined) {
      setError(formatMessage({ id: 'ai-agents.modal.temperature-error' }));
      return;
    }

    const draft = {
      name,
      modelSlug,
      systemPrompt,
      temperature: parsedTemperature,
      maxTokens: editAgent?.maxTokens ?? null,
      photo: editAgent?.photo ?? null,
      isActive: editAgent?.isActive ?? true,
    };

    if (editAgent) {
      dispatch(updateAiAgent({ ...editAgent, ...draft }));
    } else {
      dispatch(createAiAgent(draft));
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCloseModal} width="sm">
      <div>
        <Header tag="p" size="6" className={styles['agent-modal__title']}>
          {editAgent
            ? formatMessage({ id: 'ai-agents.modal.edit-title' })
            : formatMessage({ id: 'ai-agents.modal.create-title' })}
        </Header>
        <p className={styles['agent-modal__description']}>{formatMessage({ id: 'ai-agents.modal.caption' })}</p>
        <form onSubmit={handleSubmit} data-autofocus-first-field>
          <InputField
            autoFocus
            value={name}
            onChange={(e) => setName(e.currentTarget.value)}
            fieldSize="md"
            title={formatMessage({ id: 'ai-agents.modal.name-label' })}
            placeholder={formatMessage({ id: 'ai-agents.modal.name-placeholder' })}
            containerClassName={styles['agent-modal__field']}
          />
          {models.length ? (
            <div className={styles['agent-modal__field']}>
              <DropdownList
                label={formatMessage({ id: 'ai-agents.modal.model-label' })}
                placeholder={formatMessage({ id: 'ai-agents.modal.model-select-placeholder' })}
                options={modelOptions}
                value={modelOptions.find((option) => option.value === modelSlug) || null}
                onChange={(option: { value: string } | null) => setModelSlug(option?.value || '')}
              />
            </div>
          ) : (
            // catalog unavailable: fall back to manual slug entry
            <InputField
              value={modelSlug}
              onChange={(e) => setModelSlug(e.currentTarget.value)}
              fieldSize="md"
              title={formatMessage({ id: 'ai-agents.modal.model-label' })}
              placeholder={formatMessage({ id: 'ai-agents.modal.model-placeholder' })}
              containerClassName={styles['agent-modal__field']}
            />
          )}
          <InputField
            value={temperature}
            onChange={(e) => setTemperature(e.currentTarget.value)}
            errorMessage={error}
            fieldSize="md"
            title={formatMessage({ id: 'ai-agents.modal.temperature-label' })}
            placeholder={formatMessage({ id: 'ai-agents.modal.temperature-placeholder' })}
            containerClassName={styles['agent-modal__field']}
          />
          <div className={styles['agent-modal__field']}>
            <p className={styles['agent-modal__label']}>{formatMessage({ id: 'ai-agents.modal.prompt-label' })}</p>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.currentTarget.value)}
              placeholder={formatMessage({ id: 'ai-agents.modal.prompt-placeholder' })}
              className={styles['agent-modal__textarea']}
              rows={5}
            />
          </div>
          <div className={styles['agent-modal__footer']}>
            <Button
              type="submit"
              label={
                editAgent
                  ? formatMessage({ id: 'ai-agents.modal.confirm-save' })
                  : formatMessage({ id: 'ai-agents.modal.confirm-create' })
              }
              buttonStyle="yellow"
              size="md"
              disabled={!name || !modelSlug}
            />
            <button type="button" className="cancel-button" onClick={handleCloseModal}>
              {formatMessage({ id: 'tenants.modal-button-cancel' })}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
