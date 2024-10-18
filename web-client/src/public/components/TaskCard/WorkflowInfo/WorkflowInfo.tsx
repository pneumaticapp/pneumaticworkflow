import * as React from 'react';

import { IWorkflowDetails } from '../../../types/workflow';
import { IntlMessages } from '../../IntlMessages';
import { TemplateName } from '../../UI/TemplateName';
import { EKickoffOutputsViewModes, KickoffOutputs } from '../../KickoffOutputs';
import { UserData } from '../../UserData';
import { Avatar } from '../../UI/Avatar';
import { getUserFullName, EXTERNAL_USER } from '../../../utils/users';
import { Header } from '../../UI/Typeography/Header';

import styles from './WorkflowInfo.css';

export interface IWorkflowInfoProps {
  workflow: IWorkflowDetails;
}

export function WorkflowInfo({ workflow }: IWorkflowInfoProps) {
  const renderStartedByUser = () => {
    return (
      <UserData userId={workflow.workflowStarter}>
        {(user) => {
          if (!user) {
            return null;
          }

          return (
            <>
              <div className={styles['section-title']}>
                <IntlMessages id="template.started-by" />
              </div>
              <div className={styles['performer']} key={user.id}>
                <Avatar size="sm" user={user} containerClassName={styles['performer__avatar']} showInitials={false} />
                <span>{getUserFullName(workflow.isExternal ? EXTERNAL_USER : user)}</span>
              </div>
            </>
          );
        }}
      </UserData>
    );
  };

  return (
    <>
      <div className={styles['process-info-general-info']}>
        <div className={styles['process-info-pretitle']}>{workflow.currentTask.name}</div>
        {workflow.name && (
          <Header size="4" tag="p" className={styles['process-info-title']}>
            {workflow.name}
          </Header>
        )}
        {workflow.description && <div className={styles['process-info-description']}>{workflow.description}</div>}
      </div>
      <div className={styles['section-title']}>
        <IntlMessages id="processes.task-template-title" />
      </div>
      <div className={styles['process-info-workflow-name']}>
        <TemplateName
          isLegacyTemplate={workflow.isLegacyTemplate}
          legacyTemplateName={workflow.legacyTemplateName}
          templateName={workflow.template?.name}
        />
      </div>
      {renderStartedByUser()}
      <KickoffOutputs
        viewMode={EKickoffOutputsViewModes.Detailed}
        containerClassName="mt-3"
        description={workflow.kickoff?.description}
        outputs={workflow.kickoff?.output}
      />
    </>
  );
}
