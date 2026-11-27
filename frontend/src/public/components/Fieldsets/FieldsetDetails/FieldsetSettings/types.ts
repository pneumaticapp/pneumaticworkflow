import type { ChangeEvent } from 'react';

import type { EFieldLabelPosition } from '../../../../types/fieldset';

export type TFieldsetSettingsProps = {
  title: string;
  description: string;
  labelPosition: EFieldLabelPosition;
  isReadOnly: boolean;
  isTitleError: boolean;
  onTitleChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onDescriptionChange: (event: ChangeEvent<HTMLTextAreaElement>) => void;
  onLabelPositionChange: (key: EFieldLabelPosition) => void;
};
