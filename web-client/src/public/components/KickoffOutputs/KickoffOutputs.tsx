/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EditIcon } from '../icons';
import { EExtraFieldType, IExtraField } from '../../types/template';

import { CheckboxOutput } from './CheckboxOutput';
import { RadioOutput } from './RadioOutput';
import { TextOutput } from './TextOutput';
import { UrlOutput } from './UrlOutput';
import { FileOutput } from './FileOutput';
import { UserOutput } from './UserOutput';
import { flatten, isArrayWithItems } from '../../utils/helpers';
import { Attachments } from '../Attachments';
import { TUploadedFile } from '../../utils/uploadFiles';
import { RichText } from '../RichText';

import styles from './KickoffOutputs.css';

export enum EKickoffOutputsViewModes {
  Detailed = 'detailed',
  Short = 'short',
}

export interface IKickoffOutputs {
  containerClassName?: string;
  description?: string | null;
  viewMode: EKickoffOutputsViewModes;
  outputs?: IExtraField[];
  onEdit?(): void;
  isOnlyAttachmentsShown?: boolean;
  isTruncated?: boolean;
}

export function KickoffOutputs({
  containerClassName,
  viewMode,
  outputs,
  description,
  onEdit,
  isOnlyAttachmentsShown = false,
  isTruncated,
}: IKickoffOutputs) {
  if (!outputs || !isArrayWithItems(outputs)) return null;

  if (isOnlyAttachmentsShown) {
    const fileOutputs = outputs.filter(({ type }) => type === EExtraFieldType.File);
    const attachments = flatten(fileOutputs.map(({ attachments }) => attachments || [])) as TUploadedFile[];
    return <Attachments attachments={attachments} />;
  }

  const { formatMessage, messages } = useIntl();

  const renderOutputsList = () => {
    const outputsMap: { [key in EExtraFieldType]: Function } = {
      [EExtraFieldType.Checkbox]: CheckboxOutput,
      [EExtraFieldType.Creatable]: RadioOutput,
      [EExtraFieldType.Date]: TextOutput,
      [EExtraFieldType.Radio]: RadioOutput,
      [EExtraFieldType.String]: TextOutput,
      [EExtraFieldType.Text]: TextOutput,
      [EExtraFieldType.Url]: UrlOutput,
      [EExtraFieldType.File]: FileOutput,
      [EExtraFieldType.User]: UserOutput,
    };

    if (isTruncated) {
      const firstOutput = outputs[0];
      const OutputComponent = outputsMap[firstOutput.type];

      return <OutputComponent {...firstOutput} />;
    }

    return outputs?.map((output, index) => {
      const OutputComponent = outputsMap[output.type];

      const isEmpty = !(
        output.value ||
        output.attachments?.length ||
        output.selections?.findIndex((selection) => selection.isSelected) !== -1
      );

      return !isEmpty ? <OutputComponent key={index} {...output} /> : null;
    });
  };

  const renderTitle = () => {
    return (
      <span className={styles['header-title']}>
        {formatMessage({ id: 'template.kick-off-form-title' })}
        {onEdit && (
          <button
            type="button"
            aria-label={messages['kickoff-output.edit.edit-kickoff'] as string}
            className={styles['header-title__edit']}
            onClick={onEdit}
          >
            <EditIcon />
          </button>
        )}
      </span>
    );
  };

  const renderDescription = () => {
    const hasDescription = Boolean(description && description.trim());

    if (!hasDescription) {
      return null;
    }

    return (
      <span className={styles['header__description']}>
        <RichText text={description || ''} />
      </span>
    );
  };

  return (
    <div className={classnames(containerClassName, styles['kickoff-outputs'])}>
      {viewMode === EKickoffOutputsViewModes.Detailed && (
        <div className={styles['kickoff-outputs__header']}>
          {renderTitle()}

          {renderDescription()}
        </div>
      )}

      {renderOutputsList()}
    </div>
  );
}
