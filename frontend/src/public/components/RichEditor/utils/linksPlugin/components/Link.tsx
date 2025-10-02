/* eslint-disable */
/* prettier-ignore */
import React, { ReactElement, ReactNode, useRef } from 'react';
import { EditorState } from 'draft-js';
import { CustomTooltip } from '../../../../UI';
import { truncateString } from '../../../../../utils/truncateString';

export interface ILinkPubProps {
  children: ReactNode;
  entityKey: string;
  getEditorState(): EditorState;
}

interface ILinkProps extends ILinkPubProps {
  className?: string;
  target?: string;
}

export const Link = ({
  children,
  className,
  entityKey,
  getEditorState,
  target,
}: ILinkProps): ReactElement => {
  const linkRef = useRef(null);
  const entity = getEditorState().getCurrentContent().getEntity(entityKey);
  const entityData = entity ? entity.getData() : undefined;
  const href = (entityData && entityData.url) || undefined;

  return (
    <>
      <a
        ref={linkRef}
        className={className}
        title={href}
        href={href}
        target={target}
        rel="noopener noreferrer"
      >
        {children}
      </a>
      <CustomTooltip
        target={linkRef}
        tooltipText={truncateString(href, 50)}
      />
    </>
  );
};
