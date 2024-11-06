/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import Truncate from 'react-truncate';
import { Form, Modal, ModalBody, ModalHeader } from 'reactstrap';
import { useIntl } from 'react-intl';
import Switch from 'rc-switch';
import moment from 'moment-timezone';

import { ELLIPSIS_CHAR } from '../../constants/defaultValues';
import { ERoutes } from '../../constants/routes';

import { history } from '../../utils/history';
import { IntlMessages } from '../IntlMessages';
import { EInputNameBackgroundColor } from '../../types/workflow';
import { IExtraField, EExtraFieldMode } from '../../types/template';
import { getPluralNoun, isArrayWithItems } from '../../utils/helpers';
import { getEditedFields } from '../TemplateEdit/ExtraFields/utils/getEditedFields';

import { getInitialKickoff } from './utils/getInitialKickoff';
import { ExtraFieldIntl } from '../TemplateEdit/ExtraFields';
import { PlayLogoIcon } from '../icons';
import { validateWorkflowName } from '../../utils/validators';
import { checkExtraFieldsAreValid } from './utils/areKickoffFieldsValid';
import { IRunWorkflow } from './types';
import { Button } from '../UI/Buttons/Button';
import { RichText } from '../RichText';
import { DateField, SectionTitle } from '../UI';
import { DateFormat } from '../UI/DateFormat';
import { reactElementToText } from '../../utils/reactElementToText';

import styles from '../Templates/Templates.css';

import { useWorkflowNameVariables } from '../TemplateEdit/TaskForm/utils/getTaskVariables';
import { InputWithVariables } from '../TemplateEdit/InputWithVariables';

export interface INullableWorkflowEditPopupProps {
  timezone: string;
  isAdmin: boolean;
  isOpen: boolean;
  isLoading: boolean;
  workflow: IRunWorkflow | null;
  accountId: number;
  closeModal(): void;
  onRunWorkflow(value: IRunWorkflow): void;
}

export interface IWorkflowEditPopupProps extends Omit<INullableWorkflowEditPopupProps, 'workflow'> {
  workflow: IRunWorkflow;
}

export function WorkflowEditPopup({ workflow, ...restProps }: INullableWorkflowEditPopupProps) {
  if (!workflow) {
    return null;
  }

  return <WorkflowEditPopupComponent workflow={workflow} {...restProps} />;
}

function WorkflowEditPopupComponent({
  isOpen,
  isLoading,
  workflow,
  timezone,
  accountId,
  isAdmin,
  closeModal,
  onRunWorkflow,
}: IWorkflowEditPopupProps) {
  const variables = useWorkflowNameVariables(workflow.kickoff);

  const { formatMessage } = useIntl();
  const [dueDate, setDueDate] = React.useState<string | null>(null);

  const descriptionLinesCount = 5;

  const [workflowName, changeWorkflowName] = React.useState(
    workflow.wfNameTemplate || `${reactElementToText(<DateFormat />)} — ${workflow.name}`,
  );
  const [kickoffState, setKickoffState] = React.useState(getInitialKickoff(workflow.kickoff));

  const [isUrgent, setIsUrgent] = React.useState(false);

  const [textExpaned, setTextExpanded] = React.useState(false);
  const expandText = React.useCallback(() => setTextExpanded(!textExpaned), [textExpaned]);

  const ellispis = (
    <a onClick={expandText} className={styles['description_more']}>
      <span className={styles['more_delimeter']}>{ELLIPSIS_CHAR}</span>
      <IntlMessages id="templates.description-more" />
    </a>
  );

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setKickoffState((prevKickoff) => {
      const newFields = getEditedFields(prevKickoff.fields, apiName, changedProps);

      return { ...prevKickoff, fields: newFields };
    });
  };

  const isWorkflowsStartButtonDisabled =
    isLoading || Boolean(validateWorkflowName(workflowName)) || !checkExtraFieldsAreValid(kickoffState?.fields);

  const handleToggleIsUrgent = () => setIsUrgent(!isUrgent);

  const renderUrgentSwitch = () => {
    const handleSwitch = () => {
      handleToggleIsUrgent?.();
    };

    return (
      <div className={styles['urgent-switch']}>
        <div className={styles['urgent-switch__label']}>{formatMessage({ id: 'workflows.card-urgent' })}</div>
        <Switch
          className={classnames(
            'custom-switch custom-switch-primary custom-switch-small ml-auto',
            styles['urgent-switch__switch'],
          )}
          checkedChildren={null}
          unCheckedChildren={null}
          onChange={handleSwitch}
          checked={isUrgent}
        />
      </div>
    );
  };

  const renderModalHeader = () => {
    return (
      <ModalHeader className={styles['popup-header']} toggle={closeModal}>
        <div className={styles['popup-pretitle']}>
          <IntlMessages id="templates.popup-header-info" />
        </div>
        <div className={styles['popup-title']}>
          {isUrgent ? (
            <div className={'urgent-badge'}>
              <IntlMessages id="workflows.card-urgent" />
            </div>
          ) : null}
          <div className={styles['popup-title__name']}>{workflow.name}</div>
        </div>
        {workflow.description && (
          <div className={styles['popup-description']}>
            <Truncate lines={!textExpaned && descriptionLinesCount} ellipsis={ellispis} trimWhitespace={true}>
              {workflow.description.split('\n').map((el, i, arr) => {
                const line = <span key={i}>{el}</span>;
                if (i === arr.length - 1) {
                  return line;
                } else {
                  return [line, <br key={`${i}br`} />];
                }
              })}
            </Truncate>
          </div>
        )}
        <div className={styles['workflow-modal-info']}>
          <div className={styles['workflow-modal-info__stats']}>
            {workflow.tasksCount && (
              <div>
                <span className={styles['workflow-modal-info__stats-amount']}>{workflow.tasksCount}</span>
                &nbsp;
                <span>
                  {getPluralNoun({
                    counter: workflow.tasksCount,
                    single: 'step',
                    plural: 'steps',
                  })}
                </span>
              </div>
            )}

            {workflow.performersCount && (
              <div>
                <span className={styles['workflow-modal-info__stats-amount']}>{workflow.performersCount}</span>
                &nbsp;
                <span>
                  {getPluralNoun({
                    counter: workflow.performersCount,
                    single: 'performer',
                    plural: 'performers',
                  })}
                </span>
              </div>
            )}
          </div>

          {renderUrgentSwitch()}
        </div>
      </ModalHeader>
    );
  };

  const renderTemplateEditButton = () => {
    const redirectToWorkflowEdit = (e: React.MouseEvent) => {
      e.preventDefault();
      const redirectUrl = ERoutes.TemplatesEdit.replace(':id', String(workflow.id));

      if (!history.location.pathname.includes(redirectUrl)) {
        history.push(redirectUrl);
      }

      closeModal();
    };

    return (
      <Button
        buttonStyle="transparent-black"
        onClick={redirectToWorkflowEdit}
        label={formatMessage({ id: 'templates.edit-template' })}
        className={styles['popup-buttons__button_edit-template']}
        size="md"
      />
    );
  };

  const handleRunWorkflow = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onRunWorkflow({
      ...workflow,
      kickoff: kickoffState,
      name: workflowName,
      isUrgent,
      dueDate: dueDate || undefined,
    });
  };

  return (
    <div className={styles['popup']}>
      <Modal
        isOpen={isOpen}
        backdrop="static"
        wrapClassName={classnames('processes-workflows-popup', styles['workflows-modal'])}
      >
        <Form onSubmit={handleRunWorkflow}>
          {renderModalHeader()}
          <ModalBody className={styles['popup-body']}>
            <div className={styles['modal-body_hint']}>
              <IntlMessages id="templates.body-hint" />
            </div>

            <InputWithVariables
              title={formatMessage({ id: 'templates.start-name' })}
              listVariables={variables}
              templateVariables={variables}
              value={workflowName || ''}
              onChange={(value) => {
                changeWorkflowName(value);

                return Promise.resolve(value);
              }}
              className={styles['workflow-name-field']}
              toolipText={formatMessage({ id: 'kickoff.workflow-name-tooltip' })}
              foregroundColor="beige"
              size="xl"
            />
            {kickoffState && isArrayWithItems(kickoffState.fields) && (
              <div className={styles['popup__kickoff']}>
                <SectionTitle className={styles['section-title']}>
                  {formatMessage({ id: 'template.kick-off-form-title' })}
                </SectionTitle>

                {kickoffState.description && (
                  <span className={styles['kickoff__description']}>
                    <RichText text={kickoffState.description} />
                  </span>
                )}
                <div className={styles['kickoff__inputs']}>
                  {kickoffState.fields.map((field) => (
                    <ExtraFieldIntl
                      key={field.apiName}
                      field={{ ...field }}
                      editField={handleEditField(field.apiName)}
                      showDropdown={false}
                      mode={EExtraFieldMode.ProcessRun}
                      labelBackgroundColor={EInputNameBackgroundColor.OrchidWhite}
                      namePlaceholder={field.name}
                      descriptionPlaceholder={field.description}
                      wrapperClassName={styles['kickoff-extra-field']}
                      accountId={accountId}
                    />
                  ))}
                </div>
              </div>
            )}

            <div>
              <SectionTitle className={styles['section-title']}>
                {formatMessage({ id: 'templates.due-date-title' })}
              </SectionTitle>
              <DateField
                value={dueDate}
                onChange={setDueDate}
                title={formatMessage({ id: 'templates.due-date-field' })}
                foregroundColor="beige"
                minDate={moment.tz(timezone).add(1, 'days').format('YYYY-MM-DD')}
              />
            </div>
            <div className={styles['popup-buttons']}>
              <Button
                buttonStyle="yellow"
                type="submit"
                disabled={isWorkflowsStartButtonDisabled}
                icon={PlayLogoIcon}
                label={formatMessage({ id: 'templates.start-submit' })}
                className={styles['popup-buttons__button']}
                size="md"
                isLoading={isLoading}
              />

              {isAdmin && renderTemplateEditButton()}
            </div>
          </ModalBody>
        </Form>
      </Modal>
    </div>
  );
}
