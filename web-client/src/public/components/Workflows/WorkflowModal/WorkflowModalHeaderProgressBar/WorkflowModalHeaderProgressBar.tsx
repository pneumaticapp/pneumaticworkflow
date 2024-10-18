/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import * as classnames from 'classnames';

import { CircleProgressBar } from '../../../CircleProgressBar';
import { EProgressbarColor, ProgressBar } from '../../../ProgressBar';
import { IWorkflowDetails } from '../../../../types/workflow';
import { WorkflowControlls } from '../../WorkflowControlls';
import { Dropdown, getDropdownItemColorClass, TDropdownOption } from '../../../UI';
import { isArrayWithItems } from '../../../../utils/helpers';

import styles from '../WorkflowModal.css';

export interface IWorkflowModalHeaderProgressBarProps {
  progress?: number;
  color: EProgressbarColor;
  workflow: IWorkflowDetails;
  workflowId: number;
  isMobile?: boolean;
  closeModal(): void;
  onWorkflowEnded?(): void;
  onWorkflowSnoozed?(): void;
  onWorkflowResumed?(): void;
  onWorkflowDeleted?(): void;
}

export function WorkflowModalHeaderProgressBar({
  progress,
  color,
  workflow,
  isMobile,
  onWorkflowEnded,
  onWorkflowSnoozed,
  onWorkflowResumed,
  onWorkflowDeleted,
}: IWorkflowModalHeaderProgressBarProps) {
  if (progress === undefined) {
    return null;
  }

  const renderControlls = () => {
    return (

      <WorkflowControlls
        workflow={workflow}
        onWorkflowDeleted={onWorkflowDeleted}
        onWorkflowEnded={onWorkflowEnded}
        onWorkflowSnoozed={onWorkflowSnoozed}
        onWorkflowResumed={onWorkflowResumed}
      >
        {controllOptions => {
          if (!isArrayWithItems(controllOptions)) {
            return null;
          }

          return (
            <div className={styles['action-buttons']}>
              {getNormalizedControlls(controllOptions).map(option => {
                const { Icon, onClick, label, subOptions, isHidden } = option;
                if (isHidden) {
                  return null;
                }

                const renderControl = (onClick?: TDropdownOption['onClick']) => {
                  const Tag = onClick ? "button" : "span";

                  return (
                    <Tag
                      onClick={onClick ? () => onClick(() => {}) : undefined}
                      className={classnames(
                        styles['action-buttons__button'],
                        getDropdownItemColorClass(option.color)
                      )}
                      children={(
                        <>
                          {Icon && <Icon />}
                          <span className={styles['action-buttons__button-text']}>{label}</span>
                        </>
                      )}
                    />
                  );
                };

                return (
                  <div className={styles['action-buttons__button-wrapper']}>
                    {!subOptions
                      ? renderControl(onClick)
                      : (
                        <Dropdown
                          renderToggle={() => renderControl()}
                          options={subOptions}
                          direction="left"
                          className={styles['dropdown-container']}
                        />
                      )}
                  </div>
                )
              })}
            </div>
          );
        }}
      </WorkflowControlls>
    );
  }

  if (isMobile) {
    return (
      <div className={styles['progress-container-mobile']}>
        <div className={styles['progress-bar-text']}>
          {`Progress ${progress}%`}
        </div>
        <ProgressBar
          progress={progress}
          background="#fdf7ee"
          color={color}
        />
        {renderControlls()}
      </div>
    );
  }

  return (
    <div className={styles['progress-container-desktop']}>
      <CircleProgressBar
        radius={49}
        bgColor="#fdF7ee"
        percent={progress}
        text={`${progress}%`}
        color={color}
      />
      {renderControlls()}
    </div>
  );
}

const getNormalizedControlls = (controlls: TDropdownOption[]): TDropdownOption[] => {
  return controlls.map(option => {
    if (option.withConfirmation && !isArrayWithItems(option.subOptions)) {
      return {
        ...option,
        withConfirmation: false,
        subOptions: [
          {
            ...option,
            withConfirmation: true,
            initialConfirmationState: "confirmation",
            withUpperline: false,
            size: "sm",
          }
        ]
      }
    }

    return option;
  });
}
