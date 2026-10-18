import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { BaseModal, ModalHeader } from '../../UI/BaseModal';
import { updateAIAgent } from '../../../redux/ai/slice';
import { CreateAIAgentForm } from './CreatePerformerModal/CreateAIAgentForm';
import type { IAIAgentFormValues } from './CreatePerformerModal/types';
import type { IEditAIAgentModalProps } from './types';

import modalStyles from './CreatePerformerModal/CreatePerformerModal.css';

export function EditAIAgentModal({ agent, onClose }: IEditAIAgentModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const initialValues: IAIAgentFormValues = {
    name: agent.name,
    providerId: String(agent.providerId),
    model: agent.model,
    systemPrompt: agent.systemPrompt,
    photo: agent.photo ?? '',
  };

  const handleSubmit = (values: IAIAgentFormValues) => {
    dispatch(
      updateAIAgent({
        id: agent.id,
        name: values.name.trim(),
        providerId: Number(values.providerId),
        model: values.model,
        systemPrompt: values.systemPrompt,
        photo: values.photo || null,
        isActive: agent.isActive,
      }),
    );
    onClose();
  };

  return (
    <BaseModal
      isOpen
      toggle={onClose}
      className={modalStyles['modal__dialog']}
      contentClassName={modalStyles['modal__content']}
    >
      <ModalHeader toggle={onClose} className={modalStyles['modal__header']}>
        {formatMessage({ id: 'team.ai-agents.edit-modal-title' })}
      </ModalHeader>

      <CreateAIAgentForm
        isActive
        isOpen
        initialValues={initialValues}
        submitLabel={formatMessage({ id: 'team.create-ai-agent-modal.save' })}
        onSubmit={handleSubmit}
      />
    </BaseModal>
  );
}
