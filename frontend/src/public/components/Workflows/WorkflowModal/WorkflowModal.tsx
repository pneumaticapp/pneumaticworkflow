import * as React from 'react';
import classnames from 'classnames';
import OutsideClickHandler from 'react-outside-click-handler';
import TextareaAutosize from 'react-textarea-autosize';
import { Modal, ModalBody } from 'reactstrap';

import {
  EWorkflowsLogSorting,
  IWorkflowDetailsClient,
  IWorkflowEdit,
  IWorkflowEditData,
  IWorkflowLogItem,
} from '../../../types/workflow';
import { IExtraField } from '../../../types/template';
import { Avatar } from '../../UI/Avatar';
import { EditIcon, ModalCloseIcon } from '../../icons';
import { EditKickoffContainer } from '../../KickoffEdit';
import { getEditKickoff } from '../../../utils/workflows';
import { getPercent } from '../../../utils/helpers';
import { getUserFullName } from '../../../utils/users';
import { IntlMessages } from '../../IntlMessages';
import { EUserStatus } from '../../../types/user';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../../KickoffOutputs';
import { Loader } from '../../UI/Loader';
import { WorkflowLog } from '../WorkflowLog';
import { WorkflowModalHeaderProgressBar } from './WorkflowModalHeaderProgressBar';
import { validateWorkflowName } from '../../../utils/validators';
import { TemplateName } from '../../UI/TemplateName';
import { getWorkflowProgressColor } from '../utils/getWorkflowProgressColor';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { UserData } from '../../UserData';
import { DateFormat } from '../../UI/DateFormat';

import styles from './WorkflowModal.css';
import {
  IChangeWorkflowLogViewSettingsPayload,
  ISendWorkflowLogComment,
  TEditWorkflowPayload,
} from '../../../redux/workflows/types';

export interface IWorkflowModalOwnProps {
  onClose?(): void;
}

export interface IWorkflowModalStoreProps {
  workflowId: number | null;
  isAccountOwner: boolean;
  sorting: EWorkflowsLogSorting;
  isCommentsShown: boolean;
  isOnlyAttachmentsShown: boolean;
  isOpen: boolean;
  timezone: string;
  dateFmt: string;
  workflow: IWorkflowDetailsClient | null;
  workflowEdit: IWorkflowEdit;
  items: IWorkflowLogItem[];
  isLoading?: boolean;
  isLogLoading: boolean;
  canEdit: boolean;
  isRunWorkflowOpen: boolean;
  isFullscreenImageOpen: boolean;
  language?: string;
  sendWorkflowLogComments(payload: ISendWorkflowLogComment): void;
  setIsEditWorkflowName(payload: boolean): void;
  setIsEditKickoff(payload: boolean): void;
  changeWorkflowLogViewSettings(payload: IChangeWorkflowLogViewSettingsPayload): void;
  editWorkflow(payload: TEditWorkflowPayload): void;
  setWorkflowEdit(payload: IWorkflowEditData): void;
  toggleModal(): void;
  onWorkflowEnded?(): void;
  onWorkflowSnoozed?(): void;
  onWorkflowResumed?(): void;
  onWorkflowDeleted?(): void;
}

export type IWorkflowModalProps = IWorkflowModalOwnProps & IWorkflowModalStoreProps;

export class WorkflowModal extends React.Component<IWorkflowModalProps> {
  private processProgress: number | undefined;

  public constructor(props: IWorkflowModalProps) {
    super(props);
    this.processProgress = this.calculateWorkflowProgress();
  }

  public componentDidMount() {
    const { workflow, setWorkflowEdit } = this.props;
    if (!workflow) {
      return;
    }

    const { name, kickoff } = workflow;
    const editWorkflow = { name, kickoff: getEditKickoff(kickoff) };

    setWorkflowEdit(editWorkflow);
  }

  public componentDidUpdate(prevProps: IWorkflowModalStoreProps) {
    const { workflow, setWorkflowEdit } = this.props;
    if (!workflow) {
      return;
    }

    const { name, kickoff } = workflow;
    const prevKickoffId = prevProps.workflow?.kickoff.id;

    if (prevKickoffId !== kickoff.id) {
      const editProcess = { name, kickoff: getEditKickoff(kickoff) };
      setWorkflowEdit(editProcess);
    }

    this.processProgress = this.calculateWorkflowProgress();
  }

  private calculateWorkflowProgress = () => {
    const { workflow } = this.props;
    if (!workflow) {
      return undefined;
    }

    const { completedTasks, tasksCountWithoutSkipped } = workflow;
    if (tasksCountWithoutSkipped) {
      return getPercent(completedTasks.length, tasksCountWithoutSkipped);
    }

    return undefined;
  };

  private renderWorkflowAsideInfo = ({ isMobile }: { isMobile: boolean }) => {
    const { workflow, workflowId, onWorkflowEnded, onWorkflowSnoozed, onWorkflowResumed, onWorkflowDeleted, language } =
      this.props;

    if (!workflowId || !workflow) {
      return null;
    }

    return (
      <WorkflowModalHeaderProgressBar
        progress={this.processProgress}
        color={getWorkflowProgressColor(
          workflow.status,
          [workflow.areOverdueTasks ? workflow.oldestDeadline : '', workflow.dueDate],
          language,
        )}
        workflow={workflow}
        workflowId={workflowId}
        closeModal={this.closeModal}
        isMobile={isMobile}
        onWorkflowEnded={onWorkflowEnded}
        onWorkflowSnoozed={onWorkflowSnoozed}
        onWorkflowResumed={onWorkflowResumed}
        onWorkflowDeleted={onWorkflowDeleted}
      />
    );
  };

  private renderWorkflowName = () => {
    const {
      workflow,
      workflowEdit: {
        isWorkflowNameEditing,
        isWorkflowNameSaving,
        workflow: workflowEditData,
        workflow: { name },
      },
      canEdit,
      setIsEditWorkflowName,
      setWorkflowEdit,
    } = this.props;

    if (!workflow) {
      return null;
    }

    const { name: initialName, isUrgent } = workflow;

    if (!isWorkflowNameEditing) {
      return (
        <div className={styles['popup-name-container']}>
          <div className={styles['popup-title']}>
            {isUrgent ? (
              <div className={styles['popup-title_urgent']}>
                <IntlMessages id="workflows.card-urgent" />
              </div>
            ) : null}
            <div className={styles['popup-title_name']}>{initialName}</div>

            {canEdit && (
              <>
                &nbsp;&nbsp;
                <button
                  type="button"
                  className={styles['popup-title__edit']}
                  onClick={() => setIsEditWorkflowName(true)}
                  aria-label="Edit workflow name"
                >
                  <EditIcon />
                </button>
              </>
            )}
          </div>
        </div>
      );
    }

    const handleEditName = (event: React.SyntheticEvent) => {
      event.preventDefault();

      const shouldNotEdit = validateWorkflowName(name) || name === initialName;
      if (shouldNotEdit) {
        setWorkflowEdit({ ...workflowEditData, name: initialName });
        setIsEditWorkflowName(false);

        return;
      }

      this.handleEditProcess({ name });
    };

    return (
      <form className={styles['popup-title-form']} onSubmit={handleEditName}>
        <Loader isLoading={isWorkflowNameSaving} />
        {isUrgent ? (
          <div className={styles['popup-title_urgent']}>
            <IntlMessages id="workflows.card-urgent" />
          </div>
        ) : null}
        <TextareaAutosize
          translate={undefined}
          autoFocus
          onBlur={handleEditName}
          value={name}
          onChange={(e) => setWorkflowEdit({ ...workflowEditData, name: e.target.value })}
          className={classnames(
            styles['popup-title-form__input'],
            isUrgent && styles['popup-title-form__input_urgent'],
          )}
        />
      </form>
    );
  };

  private renderKickoff = () => {
    const {
      workflow,
      workflowEdit: {
        isKickoffEditing,
        isKickoffSaving,
        workflow: { kickoff: editKickoff },
        workflow: workflowEditData,
      },
      setIsEditKickoff,
      setWorkflowEdit,
      canEdit,
    } = this.props;

    if (!workflow) {
      return null;
    }
    const { kickoff: initialKickoff } = workflow;
    if (!initialKickoff || !editKickoff) {
      return null;
    }

    const initialEditKickoff = getEditKickoff(initialKickoff);

    if (!isKickoffEditing) {
      return (
        <KickoffOutputs
          viewMode={EKickoffOutputsViewModes.Detailed}
          containerClassName="mt-3"
          description={initialKickoff?.description}
          outputs={initialKickoff?.output}
          onEdit={canEdit ? () => setIsEditKickoff(true) : undefined}
        />
      );
    }

    const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
      const newKickoffFields = getEditedFields(editKickoff.fields, apiName, changedProps);
      const newKickoff = { ...editKickoff, fields: newKickoffFields };

      setWorkflowEdit({ ...workflowEditData, kickoff: newKickoff });
    };

    const handleCancel = () => {
      setWorkflowEdit({ ...workflowEditData, kickoff: initialEditKickoff });
      setIsEditKickoff(false);
    };

    return (
      <div className={styles['kickoff-edit']}>
        <EditKickoffContainer
          isLoading={isKickoffSaving}
          kickoff={editKickoff}
          onEditField={handleEditField}
          onSave={() => this.handleEditProcess({ kickoff: editKickoff })}
          onCancel={handleCancel}
        />
      </div>
    );
  };

  private handleEditProcess = ({ name, kickoff }: IWorkflowEditData) => {
    const { workflowId, editWorkflow } = this.props;

    editWorkflow({ name, kickoff, workflowId: workflowId as number });
  };

  private closeModal = () => {
    const { toggleModal, onClose } = this.props;

    toggleModal();
    onClose?.();
  };

  private renderContent = () => {
    const {
      sorting,
      isCommentsShown,
      isOnlyAttachmentsShown,
      workflow,
      items,
      workflowId,
      isLoading,
      changeWorkflowLogViewSettings,
      sendWorkflowLogComments,
      isLogLoading,
    } = this.props;

    if (isLoading) {
      return (
        <div
          className={classnames('w-100', styles['popup-header'])}
          onClick={this.closeModal}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              this.closeModal();
            }
          }}
          aria-label="Close workflow modal"
        >
          <Loader isLoading />
        </div>
      );
    }

    if (!workflow) return <div></div>;

    return (
      <>
        <div className={classnames(styles['popup-header'])}>
          <ModalCloseIcon onClick={this.closeModal} className={styles['close-icon']} />

          <div className={styles['header-popup-body']}>
            <div className={styles['popup-general-info-container']}>
              <div className={styles['popup-general-info']}>
                <div className={styles['popup-title-container']}>
                  <div className={styles['popup-pretitle']}>
                    <TemplateName
                      isLegacyTemplate={workflow.isLegacyTemplate}
                      legacyTemplateName={workflow.legacyTemplateName}
                      templateName={workflow.template?.name}
                    />
                  </div>
                  {this.renderWorkflowName()}
                  {this.renderWorkflowInfo()}
                  {this.renderDescription()}
                </div>
              </div>
              {this.renderKickoff()}
              {this.renderWorkflowAsideInfo({ isMobile: true })}
            </div>
            {this.renderWorkflowAsideInfo({ isMobile: false })}
          </div>
        </div>
        <ModalBody className={classnames(styles['popup-body'])}>
          <WorkflowLog
            theme="white"
            items={items}
            sorting={sorting}
            isLoading={isLogLoading}
            isCommentsShown={isCommentsShown}
            isOnlyAttachmentsShown={isOnlyAttachmentsShown}
            workflowId={workflowId}
            changeWorkflowLogViewSettings={changeWorkflowLogViewSettings}
            includeHeader
            sendComment={sendWorkflowLogComments}
            workflowStatus={workflow.status}
            onClickTask={this.closeModal}
            areTasksClickable
          />
        </ModalBody>
      </>
    );
  };

  private renderDescription = () => {
    const { workflow } = this.props;
    const workflowDescription = workflow?.description;

    if (workflowDescription) {
      return <div className={styles['popup-description']}>{workflowDescription}</div>;
    }

    return null;
  };

  private renderWorkflowInfo = () => {
    const { workflow } = this.props;
    if (!workflow) return null;

    return (
      <div className={styles['workflow-info']}>
        <UserData userId={workflow?.workflowStarter}>
          {(user) => {
            if (!user) {
              return null;
            }

            const userData =
              workflow && workflow.isExternal
                ? {
                  status: EUserStatus.External,
                  email: '',
                  firstName: 'External User',
                  lastName: '',
                  photo: '',
                }
                : user;

            return (
              <div className={styles['workflow-starter']}>
                <Avatar
                  user={userData}
                  containerClassName={styles['workflow-starter__avatar']}
                  showInitials={false}
                  size="sm"
                />
                <span className={styles['workflow-starter__name']}>{getUserFullName(userData)}</span>
              </div>
            );
          }}
        </UserData>

        <p className={styles['workflow-date-started']}>
          <IntlMessages
            id="workflows.card-started"
            values={{
              date: (
                <span className={styles['workflow-date-started__date']}>
                  <DateFormat date={workflow.dateCreated} />
                </span>
              ),
            }}
          />
        </p>
      </div>
    );
  };

  public render() {
    const { isOpen, isRunWorkflowOpen, isFullscreenImageOpen } = this.props;

    return (
      <div className={styles['popup']}>
        <Modal
          isOpen={isOpen}
          toggle={this.closeModal}
          backdrop="static"
          wrapClassName={classnames('processes-workflows-popup', 'processes-inwork-popup', styles['inwork-popup'])}
          className={styles['inwork-popup-dialog']}
          contentClassName={classnames(styles['inwork-popup-content'])}
        >
          <OutsideClickHandler disabled={isRunWorkflowOpen || isFullscreenImageOpen} onOutsideClick={this.closeModal}>
            {this.renderContent()}
          </OutsideClickHandler>
        </Modal>
      </div>
    );
  }
}
