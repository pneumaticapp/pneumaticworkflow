import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';

import { useDelayUnmount } from '../../hooks/useDelayUnmount';
import {
  closeTuneViewModal,
  setFilterSelectedFields as setWorkflowsFilterSelectedFields,
  saveWorkflowsPreset,
} from '../../redux/workflows/slice';

import { IExtraField, TOrderedFields, TTransformedTask } from '../../types/template';
import { Button, Checkbox, SideModal, Tooltip } from '../UI';
import { ShortArrowIcon } from '../icons';
import { StepName } from '../StepName';

import styles from './TuneViewModal.css';
import { TooltipRichContent } from '../TemplateEdit/TooltipRichContent';
import { TSystemField } from '../Workflows/WorkflowsTablePage/WorkflowsTable/types';
import { getIsTuneViewModalOpen, getSavedFields, getWorkflowTemplatesIdsFilter } from '../../redux/selectors/workflows';
import { getTemplatesTasks, getTemplatesVariables } from '../../redux/selectors/templates';

export function TuneViewModal() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set());
  const [openedTasks, setOpenedTasks] = useState<Set<string>>(new Set());

  const isOpen = useSelector(getIsTuneViewModalOpen);
  const templatesIdsFilter = useSelector(getWorkflowTemplatesIdsFilter);

  const templateId = templatesIdsFilter[0];

  const templateTasks: TTransformedTask[] = useSelector(getTemplatesTasks(templateId));
  const savedFields = useSelector(getSavedFields);
  const variables = useSelector(getTemplatesVariables(templateId));

  useEffect(() => {
    if (isOpen && templateId) {
      const savedFieldsSet = new Set(savedFields);
      setSelectedFields(savedFieldsSet);

      const tasksToOpen = new Set<string>();
      templateTasks?.forEach((task) => {
        const hasSelectedFields = task.mergedOutputs?.some((output) => {
          if (output.kind === 'fieldset') {
            return output.data.fields.some((field) => savedFieldsSet.has(field.apiName));
          }

          return savedFieldsSet.has(output.field.apiName);
        });
        if (hasSelectedFields) {
          tasksToOpen.add(task.apiName);
        }
      });
      setOpenedTasks(tasksToOpen);
    }
  }, [isOpen, templateId, templateTasks, savedFields]);

  const shouldRender = useDelayUnmount(isOpen, 150);
  if (!shouldRender) {
    return null;
  }

  const STYLES = {
    container: styles['tune-view-modal__container'],
    header: styles['tune-view-modal__header'],
    body: styles['tune-view-modal__body'],
    taskBoxTitle: styles['tune-view-modal__task-box-title'],
    taskTitle: styles['tune-view-modal__task-title'],
    taskArrow: styles['tune-view-modal__task-arrow'],
    taskArrowRotated: styles['tune-view-modal__task-arrow-rotated'],
    fieldsContainer: styles['tune-view-modal__fields-container'],
    fieldItem: styles['tune-view-modal__field-item'],
    label: styles['tune-view-modal__label'],
    labelClassName: styles['tune-view-modal__label-class-name'],
    fieldName: styles['tune-view-modal__field-name'],
    footer: styles['tune-view-modal__footer'],
    footerButton: styles['footer-button'],
    tooltip: styles['tune-view-modal__tooltip'],
    fieldsetGroup: styles['tune-view-modal__fieldset-group'],
    fieldsetTitle: styles['tune-view-modal__fieldset-title'],
  };
  const MESSAGES = {
    title: 'workflow.tune-view-modal-title',
    applyChanges: 'workflow.tune-view-modal-applay-changes',
    saveForAll: 'workflow.tune-view-modal-save-for-all',
  };

  const handleClose = () => {
    dispatch(closeTuneViewModal());
  };

  const getNewSet = <T,>(prev: Set<T>, item: T) => {
    const newSet = new Set(prev);
    if (newSet.has(item)) {
      newSet.delete(item);
    } else {
      newSet.add(item);
    }
    return newSet;
  };

  const toggleTask = (taskApiName: string) => {
    setOpenedTasks((prev) => getNewSet(prev, taskApiName));
  };

  const onFieldToggle = (fieldId: string) => {
    setSelectedFields((prev) => getNewSet(prev, fieldId));
  };

  const isSystemField = (field: IExtraField | TSystemField): field is TSystemField => {
    return 'hasNotTooltip' in field && 'isDisabled' in field;
  };

  const handleApplyChanges = (type: 'personal' | 'account') => {
    const orderedFields: TOrderedFields[] = [];
    let orderIndex = 0;
    templateTasks.forEach(({ mergedOutputs }) => {
      mergedOutputs.forEach((output) => {
        if (output.kind === 'fieldset') {
          output.data.fields.forEach(({ apiName }) => {
            if (selectedFields.has(apiName)) {
              orderedFields.push({ order: (orderIndex += 1), width: 1, apiName });
            }
          });
        } else if (selectedFields.has(output.field.apiName)) {
          orderedFields.push({ order: (orderIndex += 1), width: 1, apiName: output.field.apiName });
        }
      });
    });

    dispatch(setWorkflowsFilterSelectedFields(Array.from(selectedFields)));
    dispatch(saveWorkflowsPreset({ orderedFields, type, templateId }));
    handleClose();
  };

  const renderFieldCheckbox = (field: IExtraField | TSystemField) => {
    const { apiName: fieldApiName, name: fieldName } = field;
    const hasNotTooltip = isSystemField(field) ? field.hasNotTooltip : null;
    const isDisabled = isSystemField(field) ? field.isDisabled : null;

    return (
      <div key={fieldApiName} className={STYLES.fieldItem}>
        <label htmlFor={fieldApiName} className={STYLES.label}>
          {hasNotTooltip ? (
            <span className={STYLES.fieldName}>{fieldName}</span>
          ) : (
            <Tooltip content={fieldName} interactive={false} contentClassName={STYLES.tooltip}>
              <span className={STYLES.fieldName}>{fieldName}</span>
            </Tooltip>
          )}
          <Checkbox
            {...(isDisabled ? { disabled: isDisabled } : {})}
            checked={selectedFields.has(fieldApiName)}
            onChange={() => onFieldToggle(fieldApiName)}
            title={fieldName}
            titlePosition="external"
            checkboxId={fieldApiName}
            labelClassName={STYLES.labelClassName}
          />
        </label>
      </div>
    );
  };

  return (
    <SideModal className={STYLES.container} onClose={handleClose} isClosing={!isOpen} nonePeddingRight>
      <SideModal.Header className={STYLES.header}>
        <div>{formatMessage({ id: MESSAGES.title })}</div>
      </SideModal.Header>

      <SideModal.Body className={STYLES.body}>
        {templateTasks?.map(({ apiName: taskApiname, name: taskName, needSteName, mergedOutputs }: TTransformedTask) => (
          <div key={taskApiname}>
            <div
              className={STYLES.taskBoxTitle}
              onClick={() => toggleTask(taskApiname)}
              onKeyDown={(e) => e.key === 'Enter' && toggleTask(taskApiname)}
              role="button"
              tabIndex={0}
            >
              <div className={STYLES.taskTitle}>
                <Tooltip
                  interactive={false}
                  content={
                    <TooltipRichContent title={taskName} subtitle={taskName} variables={variables || []} hideTitle />
                  }
                >
                  {needSteName ? (
                    <div>
                      <StepName initialStepName={taskName} templateId={templateId} />
                    </div>
                  ) : (
                    <span>{taskName}</span>
                  )}
                </Tooltip>
              </div>

              <div className={`${STYLES.taskArrow} ${openedTasks.has(taskApiname) && STYLES.taskArrowRotated}`}>
                <ShortArrowIcon />
              </div>
            </div>

            <div>
              {openedTasks.has(taskApiname) && (
                <div className={mergedOutputs.length > 0 ? STYLES.fieldsContainer : ''}>
                  {mergedOutputs.map((output) => {
                    if (output.kind === 'fieldset') {
                      return (
                        <div key={output.data.apiNameBinding} className={STYLES.fieldsetGroup}>
                          <div className={STYLES.fieldsetTitle}>{output.data.name}</div>
                          {output.data.fields.map(renderFieldCheckbox)}
                        </div>
                      );
                    }

                    return renderFieldCheckbox(output.field);
                  })}
                </div>
              )}
            </div>
          </div>
        ))}
      </SideModal.Body>

      <SideModal.Footer className={STYLES.footer}>
        <Button
          buttonStyle="yellow"
          label={formatMessage({ id: MESSAGES.applyChanges })}
          className={STYLES.footerButton}
          onClick={() => handleApplyChanges('personal')}
        />
        <Button
          buttonStyle="transparent-yellow"
          label={formatMessage({ id: MESSAGES.saveForAll })}
          className={STYLES.footerButton}
          onClick={() => handleApplyChanges('account')}
        />
      </SideModal.Footer>
    </SideModal>
  );
}
