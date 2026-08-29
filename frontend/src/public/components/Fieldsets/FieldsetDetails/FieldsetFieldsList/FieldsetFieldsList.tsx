import * as React from 'react';
import { useMemo } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../../types/template';
import { EInputNameBackgroundColor, EMoveDirections } from '../../../../types/workflow';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import { ExtraFieldsMap } from '../../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../../../TemplateEdit/ExtraFields';
import { ArrowDropdownIcon, DateIcon, LinkIcon } from '../../../icons';

import { useCheckDevice } from '../../../../hooks/useCheckDevice';

import { getSortedFields, createField, editField, deleteFieldWithCleanup, moveField } from './utils';
import { IFieldsetFieldsListProps } from './types';
import { SINGLE_LINE_FIELD_TYPES } from '../constants';
import fieldsetDetailsStyles from '../FieldsetDetails.css';
import styles from './FieldsetFieldsList.css';

const READONLY_FIELD_ICONS: Partial<Record<EExtraFieldType, React.FC<React.SVGAttributes<SVGElement>>>> = {
  [EExtraFieldType.User]: ArrowDropdownIcon,
  [EExtraFieldType.Date]: DateIcon,
  [EExtraFieldType.Url]: LinkIcon,
};

export function FieldsetFieldsList({
  fields,
  onFieldsChange,
  isReadOnly,
  labelPosition,
  accountId,
  datasetOptions,
  onCreateFieldRule: createFieldRule,
}: IFieldsetFieldsListProps) {
  const { formatMessage } = useIntl();
  const { isDesktop } = useCheckDevice();

  const sortedFields = useMemo(() => getSortedFields(fields), [fields]);

  return (
    <div className={fieldsetDetailsStyles['list']}>
      <h2 className={fieldsetDetailsStyles['section-title']}>
        {formatMessage({ id: 'fieldsets.fields-section' })}
        {isReadOnly && (
          <span className={fieldsetDetailsStyles['readonly-badge']}>
            {formatMessage({ id: 'fieldsets.readonly-badge' })}
          </span>
        )}
      </h2>

      <div className={classnames(styles['components'], isReadOnly && styles['components_disabled'])}>
        {ExtraFieldsMap.map((x) => (
          <ExtraFieldIcon
            {...x}
            key={x.id}
            onClick={() => onFieldsChange(createField(fields, x.id, formatMessage))}
            disabled={isReadOnly}
          />
        ))}
      </div>

      {sortedFields.length > 0 && (
        <div className={classnames(styles['fields'], isReadOnly && styles['fieldset_readonly'])}>
          {sortedFields.map((field, index) => {
            const readOnlyField =
              isReadOnly && SINGLE_LINE_FIELD_TYPES.has(field.type)
                ? { ...field, type: EExtraFieldType.Text }
                : field;

            const IconComponent = isReadOnly && READONLY_FIELD_ICONS[field.type];

            return (
              <ExtraFieldIntl
                key={field.apiName}
                id={index}
                field={readOnlyField}
                fieldsCount={sortedFields.length}
                labelBackgroundColor={EInputNameBackgroundColor.White}
                deleteField={() => onFieldsChange(deleteFieldWithCleanup(sortedFields, field.apiName))}
                moveFieldUp={() => onFieldsChange(moveField(sortedFields, index, EMoveDirections.Up))}
                moveFieldDown={() => onFieldsChange(moveField(sortedFields, index, EMoveDirections.Down))}
                editField={(changedProps: Partial<IExtraField>) =>
                  onFieldsChange(editField(sortedFields, field.apiName, changedProps))
                }
                accountId={accountId}
                mode={EExtraFieldMode.Kickoff}
                showDropdown
                isDisabled={isReadOnly}
                isFieldsetReadOnly={isReadOnly}
                datasetOptions={datasetOptions}
                labelPosition={isDesktop ? labelPosition : EFieldLabelPosition.Top}
                {...(IconComponent && { icon: <IconComponent /> })}
                {...(createFieldRule && {
                  onOpenFieldRules: () => createFieldRule(field.apiName),
                })}
              />
            );
          })}
        </div>
      )}

      {sortedFields.length === 0 && (
        <p className={fieldsetDetailsStyles['empty-text']}>{formatMessage({ id: 'fieldsets.no-fields' })}</p>
      )}
    </div>
  );
}
