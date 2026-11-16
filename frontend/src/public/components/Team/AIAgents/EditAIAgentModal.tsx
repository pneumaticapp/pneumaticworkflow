import * as React from 'react';
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { BaseModal, ModalHeader } from '../../UI/BaseModal';
import { updateAIAgent } from '../../../redux/ai/slice';
import { AIAgentForm } from './AIAgentForm';
import type { IAIAgentFormValues } from './AIAgentForm/types';
import type { IEditAIAgentModalProps } from './types';

import modalStyles from '../PerformerModal.css';

export function EditAIAgentModal({ agent, onClose }: IEditAIAgentModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const [isSaving, setIsSaving] = useState(false);

  const initialValues: IAIAgentFormValues = {
    name: agent.name,
    providerId: String(agent.providerId),
    model: agent.model,
    systemPrompt: agent.systemPrompt,
    photo: agent.photo ?? '',
  };

  const handleClose = () => {
    if (!isSaving) onClose();
  };

  const handleSubmit = (values: IAIAgentFormValues) => {
    setIsSaving(true);
    dispatch(
      updateAIAgent({
        id: agent.id,
        name: values.name.trim(),
        providerId: Number(values.providerId),
        model: values.model,
        systemPrompt: values.systemPrompt,
        photo: values.photo || null,
        isActive: agent.isActive,
        onSuccess: onClose,
        onError: () => setIsSaving(false),
      }),
    );
  };

  return (
    <BaseModal
      isOpen
      toggle={handleClose}
      className={modalStyles['performer-modal__dialog']}
      contentClassName={modalStyles['performer-modal__content']}
    >
      <ModalHeader toggle={handleClose} className={modalStyles['performer-modal__header']}>
        {formatMessage({ id: 'team.ai-agents.edit-modal-title' })}
      </ModalHeader>

      <AIAgentForm
        isVisible
        initialValues={initialValues}
        isSubmitting={isSaving}
        submitLabel={formatMessage({ id: 'team.create-ai-agent-modal.save' })}
        onSubmit={handleSubmit}
      />
    </BaseModal>
  );
}
