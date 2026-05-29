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
  const parts = buildRuntimeMergedOutputParts(fields, fieldsets);

  return (
    <>
      {parts.map((part) => {
        if (part.kind === 'field') {
          return (
            <ExtraFieldIntl
              key={part.field.apiName}
              field={{ ...part.field }}
              editField={onEditField(part.field.apiName)}
              showDropdown={false}
              mode={EExtraFieldMode.ProcessRun}
              labelBackgroundColor={labelBackgroundColor}
              namePlaceholder={part.field.name}
              descriptionPlaceholder={part.field.description}
              wrapperClassName={fieldClassName}
              accountId={accountId}
              labelPosition={EFieldLabelPosition.Top}
            />
          );
        }
        if (part.kind === 'fieldset') {
          return (
          <FieldsetFieldGroup
            key={part.data.apiName}
            title={part.data.name}
            description={part.data.description}
            fields={part.data.fields}
            onEditField={onEditFieldsetField}
            mode={EExtraFieldMode.ProcessRun}
            labelBackgroundColor={labelBackgroundColor}
            accountId={accountId}
            fieldClassName={fieldClassName}
            labelPosition={isDesktop ? part.data.labelPosition : EFieldLabelPosition.Top}
          />
          );
        }

        return null;
      })}
    </>
  );
}
