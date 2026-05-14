/* eslint-disable */
import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EditIcon } from '../icons';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../types/template';
import { TOutputItem } from './types';

import { CheckboxOutput } from './CheckboxOutput';
import { RadioOutput } from './RadioOutput';
import { TextOutput } from './TextOutput';
import { UrlOutput } from './UrlOutput';
import { FileOutput } from './FileOutput';
import { UserOutput } from './UserOutput';
import { isArrayWithItems } from '../../utils/helpers';
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
  fieldsets: IFieldsetData[];
  onEdit?(): void;
  isOnlyAttachmentsShown?: boolean;
  isTruncated?: boolean;
}

export function KickoffOutputs({
  containerClassName,
  viewMode,
  outputs,
  fieldsets,
  description,
  onEdit,
  isOnlyAttachmentsShown = false,
  isTruncated,
}: IKickoffOutputs) {
  if ((!outputs || !isArrayWithItems(outputs)) && !isArrayWithItems(fieldsets)) return null;


  const orderedOutputs: TOutputItem[] = [
    ...(outputs || []).map((field): TOutputItem => ({ kind: 'field', order: field.order, data: field })),
    ...(fieldsets || []).map((fs): TOutputItem => ({ kind: 'fieldset', order: fs.order, data: fs })),
  ].sort((a, b) => b.order - a.order);

  if (isOnlyAttachmentsShown) {
    const fileAttachments = orderedOutputs.flatMap((item) => {
      if (item.kind === 'field') {
        return item.data.type === EExtraFieldType.File ? (item.data.attachments || []) : [];
      }

      return item.data.fields
        .filter(({ type }) => type === EExtraFieldType.File)
        .flatMap(({ attachments }) => attachments || []);
    }) as TUploadedFile[];

    return <Attachments attachments={fileAttachments} />;
  }

  const { formatMessage, messages } = useIntl();

  const outputsMap: { [key in EExtraFieldType]: Function } = {
    [EExtraFieldType.Number]: TextOutput,
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

  const renderSingleOutput = (output: IExtraField, key: string | number) => {
    const OutputComponent = outputsMap[output.type];
    const value = output.type === EExtraFieldType.User ? output.userId || output.groupId : output.value;
    const hasValue = Array.isArray(value) ? value.length > 0 : Boolean(value);
    const isEmpty = !(hasValue || output.attachments?.length);
    return !isEmpty ? <OutputComponent key={key} {...output} /> : null;
  };

  const renderFieldsetGroup = (fieldset: IFieldsetData, children: React.ReactNode, key?: string) => (
    <div key={key} className={styles['fieldset-output-group']}>
      {fieldset.name && <p className={styles['fieldset-output-group__title']}>{fieldset.name}</p>}
      {fieldset.description && <p className={styles['fieldset-output-group__description']}>{fieldset.description}</p>}
      {children}
    </div>
  );

  const renderOutputsList = () => {
    if (isTruncated && orderedOutputs.length > 0) {
      const firstItem = orderedOutputs[0];
      if (firstItem.kind === 'field') {
        return renderSingleOutput(firstItem.data, 'truncated-field');
      }

      if (firstItem.data.fields.length) {
        const fieldset = firstItem.data;
        return renderFieldsetGroup(
          fieldset,
          renderSingleOutput(fieldset.fields[0], 'truncated-fieldset-field'),
        );
      }
    }

    return (
      <>
        {orderedOutputs.map((item, index) => {
          if (item.kind === 'field') {
            return renderSingleOutput(item.data, `field-${item.data.apiName || index}`);
          }

          const fieldset = item.data;

          return renderFieldsetGroup(
            fieldset,
            fieldset.fields.map((output, fieldIndex) =>
              renderSingleOutput(output, `fieldset-${fieldset.id}-${output.apiName || fieldIndex}`),
            ),
            `fieldset-${fieldset.id}`,
          );
        })}
      </>
    );
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

