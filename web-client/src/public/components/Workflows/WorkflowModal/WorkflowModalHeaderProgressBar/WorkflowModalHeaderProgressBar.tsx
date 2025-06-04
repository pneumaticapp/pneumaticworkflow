import * as React from 'react';
import classnames from 'classnames';

import { ConfirmableDropdownItem } from '../../../UI/Dropdown/ConfirmableDropdownItem';
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
        {(controllOptions) => {
          if (!isArrayWithItems(controllOptions)) {
            return null;
          }

          return (
            <div className={styles['action-buttons']}>
              {getNormalizedControlls(controllOptions).map((option) => {
                const { Icon, onClick, label, mapKey, subOptions, isHidden } = option;
                if (isHidden) {
                  return null;
                }

                const renderControl = (lOnClick?: TDropdownOption['onClick']) => {
                  const Tag = lOnClick ? 'button' : 'span';

                  return (
                    <Tag
                      onClick={lOnClick ? () => lOnClick(() => {}) : undefined}
                      className={classnames(styles['action-buttons__button'], getDropdownItemColorClass(option.color))}
                    >
                      <>
                        {Icon && <Icon />}
                        <span className={styles['action-buttons__button-text']}>{label}</span>
                      </>
                    </Tag>
                  );
                };
                const labelWithConfirmation = option.label === 'Delete' || option.label === 'End workflow';

                return (
                  <div
                    key={typeof label === 'string' ? label : mapKey}
                    className={styles['action-buttons__button-wrapper']}
                  >
                    {labelWithConfirmation && (
                      <ConfirmableDropdownItem
                        withConfirmation
                        initialConfirmationState="option"
                        closeDropdown={() => {}}
                        cssModule={{
                          'dropdown-item': classnames(
                            styles['action-buttons__button'],
                            getDropdownItemColorClass(option.color),
                          ),
                        }}
                        onClick={() => onClick && onClick(() => {})}
                        toggle={false}
                        tag="button"
                      >
                        <>
                          {Icon && <Icon />}
                          <span className={styles['action-buttons__button-text']}>{label}</span>
                        </>
                      </ConfirmableDropdownItem>
                    )}
                    {subOptions && (
                      <Dropdown
                        renderToggle={() => renderControl()}
                        options={subOptions}
                        direction="left"
                        className={styles['dropdown-container']}
                      />
                    )}
                    {!subOptions && !labelWithConfirmation && renderControl(onClick)}
                  </div>
                );
              })}
            </div>
          );
        }}
      </WorkflowControlls>
    );
  };

  if (isMobile) {
    return (
      <div className={styles['progress-container-mobile']}>
        <div className={styles['progress-bar-text']}>{`Progress ${progress}%`}</div>
        <ProgressBar progress={progress} background="#fdf7ee" color={color} />
        {renderControlls()}
      </div>
    );
  }

  return (
    <div className={styles['progress-container-desktop']}>
      <CircleProgressBar radius={49} bgColor="#fdF7ee" percent={progress} text={`${progress}%`} color={color} />
      {renderControlls()}
    </div>
  );
}

const getNormalizedControlls = (controlls: TDropdownOption[]): TDropdownOption[] => {
  return controlls.map((option) => {
    if (option.withConfirmation && Array.isArray(option.subOptions) && !isArrayWithItems(option.subOptions)) {
      return {
        ...option,
        withConfirmation: false,
        subOptions: [
          {
            ...option,
            withConfirmation: true,
            initialConfirmationState: 'confirmation',
            withUpperline: false,
            size: 'sm',
          },
        ],
      };
    }

    return option;
  });
};
