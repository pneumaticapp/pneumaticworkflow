import React, { FormEvent, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { closeAiAgentModal, createAiAgent, updateAiAgent } from '../../../redux/actions';
import { getAiAgentsEditModal } from '../../../redux/selectors/aiAgents';
import { Button, Header, InputField, Modal } from '../../UI';

import styles from './AiAgentModal.css';

const MAX_TEMPERATURE = 2;

export function AiAgentModal() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const { isOpen, editAgent } = useSelector(getAiAgentsEditModal);

  const [name, setName] = useState('');
  const [modelSlug, setModelSlug] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [temperature, setTemperature] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setName(editAgent?.name || '');
    setModelSlug(editAgent?.modelSlug || '');
    setSystemPrompt(editAgent?.systemPrompt || '');
    setTemperature(editAgent?.temperature != null ? String(editAgent.temperature) : '');
    setError('');
  }, [editAgent, isOpen]);

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
          <InputField
            value={modelSlug}
            onChange={(e) => setModelSlug(e.currentTarget.value)}
            fieldSize="md"
            title={formatMessage({ id: 'ai-agents.modal.model-label' })}
            placeholder={formatMessage({ id: 'ai-agents.modal.model-placeholder' })}
            containerClassName={styles['agent-modal__field']}
          />
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
