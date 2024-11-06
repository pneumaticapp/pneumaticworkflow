import React, { useEffect, useRef, useState } from 'react';
import { useIntl } from 'react-intl';

import { Button, Header, InputField, Modal } from '../UI';
import { TGenerateAITemplatePayload } from '../../redux/actions';
import { ITemplate, ITemplateTask, TAITemplateGenerationStatus } from '../../types/template';
import { useDidUpdateEffect } from '../../hooks/useDidUpdateEffect';
import { InfiniteLoader } from '../InfiniteLoader';

import styles from './TemplateAIModal.css';

export interface ITemplateAIModalProps {
  isOpen: boolean;
  generationStatus: TAITemplateGenerationStatus;
  generatedTemplate: ITemplate | null;
  generateTemplate(payload: TGenerateAITemplatePayload): void;
  stopTemplateGeneration(): void;
  setIsModalOpened(isOpened: boolean): void;
  applyTemplate(): void;
  setTemplateGenerationStatus(status: TAITemplateGenerationStatus): void;
}

export function TemplateAIModal({
  isOpen,
  generatedTemplate,
  generationStatus,
  generateTemplate,
  stopTemplateGeneration,
  setIsModalOpened,
  applyTemplate,
  setTemplateGenerationStatus,
}: ITemplateAIModalProps) {
  const { formatMessage } = useIntl();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [description, setDescription] = useState('');
  const [renderedTemplate, setRenderedTemplate] = useState<ITemplate | null>(null);
  const [heightContainer, setHeightContainer] = useState(0);
  const [activeTask, setActiveTask] = useState(0);

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  useDidUpdateEffect(() => {
    if (generationStatus === 'generated') {
      setRenderedTemplate(generatedTemplate);
    } else {
      setHeightContainer(0);
    }
  }, [generationStatus]);

  const handleClose = () => {
    setDescription('');
    setIsModalOpened(false);

    if (generationStatus === 'generating') {
      stopTemplateGeneration();
    }

    setTemplateGenerationStatus('initial');
    // Add a delay to remove data only when modal animation is finished
    setTimeout(() => setRenderedTemplate(null), 200);
  };

  const handleGenerateTemplate: React.FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    generateTemplate({ description });
  };

  const handleStopTemplateGeneration = (event: React.MouseEvent<Element, MouseEvent>) => {
    event.stopPropagation();
    event.preventDefault();
    stopTemplateGeneration();
  };

  const handleApplyTemplate = () => {
    applyTemplate();
    handleClose();
  };

  const renderLoader = () => {
    return (
      <div className={styles['ai-generate__loader']}>
        <InfiniteLoader />
      </div>
    );
  };

  const onChangeHeightContainer = (height: number) => {
    setHeightContainer(heightContainer + height);
  };

  const onActiveTask = (index: number) => {
    setActiveTask(index);
  };

  const renderTemplate = () => {
    if (!renderedTemplate) {
      return null;
    }

    const tasks = renderedTemplate.tasks.map((task, index, arr) => {
      return (
        <AnimationTask
          lastItem={index === arr.length - 1}
          key={task.id}
          order={index}
          task={task}
          onChangeHeightContainer={onChangeHeightContainer}
          onActiveTask={onActiveTask}
        />
      );
    });

    return (
      <div>
        <Button
          type="button"
          label={formatMessage({ id: 'ai-template.button-apply' })}
          buttonStyle="black"
          size="md"
          className={styles['ai-generate__cta']}
          onClick={handleApplyTemplate}
        />

        <div style={{ height: heightContainer }} className={styles['ai-generate__data']}>
          {tasks}
        </div>

        {renderedTemplate.tasks.length - 1 === activeTask && (
          <Button
            type="button"
            label={formatMessage({ id: 'ai-template.button-apply' })}
            buttonStyle="black"
            size="md"
            className={styles['ai-generate__cta']}
            onClick={handleApplyTemplate}
          />
        )}
      </div>
    );
  };

  const renderData = () => {
    if (generationStatus === 'initial') {
      return null;
    }

    return (
      <div className={styles['ai-generate__container']}>
        {generationStatus === 'generating' ? renderLoader() : renderTemplate()}
      </div>
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} width="lg">
      <div>
        <Header tag="p" size="4" className={styles['ai-generate__title']}>
          {formatMessage({ id: 'ai-template.title' })}
        </Header>

        <p className={styles['ai-generate__caption']}>{formatMessage({ id: 'ai-template.description' })}</p>

        <form onSubmit={handleGenerateTemplate} className={styles['form-ai-generate']}>
          <InputField
            value={description}
            onChange={(e) => setDescription(e.currentTarget.value)}
            fieldSize="md"
            className={styles['form__input']}
            placeholder={formatMessage({ id: 'ai-template.input-placeholder' })}
            inputRef={inputRef}
          />

          {generationStatus !== 'generating' ? (
            <Button
              type="submit"
              label={formatMessage({ id: 'ai-template.button-generate' })}
              buttonStyle="yellow"
              size="md"
              className={styles['form-ai-generate__button']}
            />
          ) : (
            <Button
              type="button"
              label={formatMessage({ id: 'ai-template.button-stop' })}
              buttonStyle="yellow"
              size="md"
              className={styles['form-ai-generate__button']}
              onClick={handleStopTemplateGeneration}
            />
          )}
        </form>
      </div>
      {renderData()}
    </Modal>
  );
}

interface IAnimationTaskProps {
  order: number;
  task: ITemplateTask;
  lastItem: boolean;
  onActiveTask(index: number): void;
  onChangeHeightContainer(height: number): void;
}

function AnimationTask({
  order,
  task: { name, description },
  lastItem,
  onChangeHeightContainer,
  onActiveTask,
}: IAnimationTaskProps) {
  const [active, setActive] = useState(false);
  const myRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    setTimeout(() => setActive(true), order * 600);
  }, []);

  useEffect(() => {
    if (myRef.current) {
      const height = myRef.current.offsetHeight + (order === 0 ? 0 : 8);
      onChangeHeightContainer(height);
      onActiveTask(order);
    }
    setTimeout(
      () => {
        myRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'center' });
      },
      lastItem ? 300 : 0,
    );
  }, [active]);

  return active ? (
    <div ref={myRef} className={styles['task']}>
      <Header tag="p" size="6" className={styles['task__name']}>
        {name}
      </Header>
      <p className={styles['task__description']}>{description}</p>
    </div>
  ) : null;
}
