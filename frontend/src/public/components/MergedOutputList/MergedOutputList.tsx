import * as React from 'react';
import { EExtraFieldMode } from '../../types/template';
import { EFieldLabelPosition } from '../../types/fieldset';
import { ExtraFieldIntl } from '../TemplateEdit/ExtraFields';
import { FieldsetFieldGroup } from '../FieldsetFieldGroup';
import { buildRuntimeMergedOutputParts } from '../TemplateEdit/TaskOutputFlow/mergeTaskOutputFlow';
import { useCheckDevice } from '../../hooks/useCheckDevice';
import { IMergedOutputListProps } from './types';

export function MergedOutputList({
  fields,
  fieldsets,
  onEditField,
  onEditFieldsetField,
  labelBackgroundColor,
  fieldClassName,
  accountId,
}: IMergedOutputListProps) {
  const { isDesktop } = useCheckDevice();
  const mergedOutputs = buildRuntimeMergedOutputParts(fields, fieldsets);

  return (
    <>
      {mergedOutputs.map((mergedOutput) => {
        if (mergedOutput.kind === 'field') {
          const fieldData = mergedOutput.field;
          const { apiName: fieldApiName, name: fieldName, description: fieldDescription } = fieldData;

          return (
            <ExtraFieldIntl
              key={fieldApiName}
              field={{ ...fieldData }}
              editField={onEditField(fieldApiName)}
              showDropdown={false}
              mode={EExtraFieldMode.ProcessRun}
              labelBackgroundColor={labelBackgroundColor}
              namePlaceholder={fieldName}
              descriptionPlaceholder={fieldDescription}
              wrapperClassName={fieldClassName}
              accountId={accountId}
              labelPosition={EFieldLabelPosition.Top}
            />
          );
        }
        if (mergedOutput.kind === 'fieldset') {
          const {
            apiName: fieldsetApiName,
            name: fieldsetName,
            description: fieldsetDescription,
            fields: fieldsetFields,
            labelPosition: fieldsetLabelPosition,
          } = mergedOutput.data;

          return (
          <FieldsetFieldGroup
            key={fieldsetApiName}
            title={fieldsetName}
            description={fieldsetDescription}
            fields={fieldsetFields}
            onEditField={onEditFieldsetField}
            mode={EExtraFieldMode.ProcessRun}
            labelBackgroundColor={labelBackgroundColor}
            accountId={accountId}
            fieldClassName={fieldClassName}
            labelPosition={isDesktop ? fieldsetLabelPosition : EFieldLabelPosition.Top}
          />
          );
        }

        return null;
      })}
    </>
  );
}
