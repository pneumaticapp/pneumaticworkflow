/* eslint-disable */
/* prettier-ignore */
import React, { MouseEvent, ReactNode } from 'react';

import { TAttachmentType } from '../../../../types/attachments';
import { IExtendedToolbarChildrenProps } from './types';
import { CustomTooltip } from '../../../UI';

interface ICreateAttachmentButtonProp {
  attachmentType: TAttachmentType;
  tooltipText: string;
  children: ReactNode;
}

interface IAttachmentButtonProp extends React.PropsWithChildren<IExtendedToolbarChildrenProps> {
  uploadAttachments(e: React.ChangeEvent<HTMLInputElement>): Promise<void>;
}

export function createAttachmentButton({ attachmentType, tooltipText, children }: ICreateAttachmentButtonProp) {
  return function AttachmentButton(props: IAttachmentButtonProp) {
    const buttonRef = React.useRef<HTMLButtonElement>(null);
    const uploadFieldRef = React.useRef<HTMLInputElement>(null);

    const preventBubblingUp = (event: MouseEvent): void => {
      event.preventDefault();
    };

    const { theme, uploadAttachments } = props;

    const inputAcceptedTypesMap: { [key in TAttachmentType]: string | undefined } = {
      file: undefined,
      image: 'image/*',
      video: 'video/*',
    };

    return (
      <div className={theme.buttonWrapper} onMouseDown={preventBubblingUp}>
        <button
          ref={buttonRef}
          className={theme.button}
          onClick={() => uploadFieldRef.current?.click()}
          type="button"
          children={children}
        />
        <CustomTooltip target={buttonRef} tooltipText={tooltipText} isModal={theme.isModal} />
        <input
          ref={uploadFieldRef}
          multiple
          onChange={async (event) => {
            await uploadAttachments(event);

            if (uploadFieldRef.current?.value) {
              uploadFieldRef.current.value = '';
            }
          }}
          type="file"
          style={{ display: 'none' }}
          accept={inputAcceptedTypesMap[attachmentType]}
        />
      </div>
    );
  };
}
