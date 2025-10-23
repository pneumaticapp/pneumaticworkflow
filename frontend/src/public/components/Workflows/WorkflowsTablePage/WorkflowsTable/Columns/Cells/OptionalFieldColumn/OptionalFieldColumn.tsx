import React from 'react';
import { useSelector } from 'react-redux';
import { CellProps } from 'react-table';

import { toDateString } from '../../../../../../../utils/dateTime';
import { IApplicationState } from '../../../../../../../types/redux';
import { TableColumns } from '../../../types';
import { EExtraFieldType, ETaskPerformerType, ITableViewFields } from '../../../../../../../types/template';
import { getUserById } from '../../../../../../UserData/utils/getUserById';
import { Avatar, TAvatarUser } from '../../../../../../UI';
import { getAttachmentTypeByFilename } from '../../../../../../Attachments/utils/getAttachmentType';
import { DocumentInfoIcon, ImageFileIcon } from '../../../../../../icons';
import { urlWithProtocolRegex } from '../../../../../../../constants/defaultValues';

import styles from './OptionalFieldColumn.css';

const IMAGE_FILE_ICON_COLOR = 'rgb(254, 195, 54)';

type TProps = React.PropsWithChildren<CellProps<TableColumns, ITableViewFields>>;

export function OptionalFieldColumn({ value }: TProps) {
  if (!value) {
    return null;
  }

  const users = useSelector((state: IApplicationState) => state.accounts.users);
  const groups = useSelector((state: IApplicationState) => state.groups.list);
  const timezone = useSelector((state: IApplicationState) => state.authUser.timezone);

  const isUrl = (str: string) => {
    return urlWithProtocolRegex.test(str);
  };

  const findBracketContent = (
    text: string,
    openBracket: string,
    closeBracket: string,
  ): { content: string; closePos: number } => {
    if (!text || !openBracket || !closeBracket) {
      throw new Error(
        `findBracketContent(): Invalid input parameters. text: "${text || 'empty'}", openBracket: "${
          openBracket || 'empty'
        }", closeBracket: "${closeBracket || 'empty'}"`,
      );
    }

    const openPos = text.indexOf(openBracket);
    if (openPos === -1) {
      throw new Error(`findBracketContent(): No opening bracket '${openBracket}' found in text: "${text}"`);
    }

    let bracketCount = 1;
    let closePos = openPos + 1;

    while (bracketCount > 0 && closePos < text.length) {
      if (text[closePos] === openBracket) bracketCount += 1;
      if (text[closePos] === closeBracket) bracketCount -= 1;
      closePos += 1;
    }

    if (bracketCount > 0) {
      throw new Error(
        `findBracketContent(): Missing closing bracket '${closeBracket}' at position ${closePos} in string: ${text}`,
      );
    }

    const content = text.slice(openPos + 1, closePos - 1);
    return { content, closePos };
  };

  const renderFileElement = (fileName: string, fileUrl: string, index: number, array: [string, string][]) => {
    const fileType = getAttachmentTypeByFilename(fileName);

    return (
      <a key={fileName} href={fileUrl} target="_blank" rel="noreferrer" className={styles['field-column__file-item']}>
        {fileType === 'image' ? (
          <ImageFileIcon fill={IMAGE_FILE_ICON_COLOR} className={styles['field-column__image-icon']} />
        ) : (
          <DocumentInfoIcon className={styles['field-column__document-icon']} />
        )}
        <span>{fileName}</span>
        {index < array.length - 1 && ', '}
      </a>
    );
  };

  const parseFileListFromMarkdown = (markdownString: string): Map<string, string> => {
    let remainingString = markdownString;
    const filesMap = new Map<string, string>();
    while (remainingString.length > 0) {
      const { content: squareBracketsContent, closePos: squareBracketsClosePos } = findBracketContent(
        remainingString,
        '[',
        ']',
      );
      remainingString = remainingString.slice(squareBracketsClosePos);

      const { content: roundBracketsContent, closePos: roundBracketsClosePos } = findBracketContent(
        remainingString,
        '(',
        ')',
      );
      remainingString = remainingString.slice(roundBracketsClosePos);

      if (isUrl(squareBracketsContent)) {
        filesMap.set(squareBracketsContent.split('/').pop() || 'file', squareBracketsContent);
      } else {
        filesMap.set(squareBracketsContent, roundBracketsContent);
      }
    }

    return filesMap;
  };

  const getFieldContent = (type: EExtraFieldType, fieldValue: ITableViewFields) => {
    if (!fieldValue || !fieldValue.value) {
      return null;
    }
    if (type === EExtraFieldType.Text) {
      return fieldValue.clearValue;
    }
    if (type === EExtraFieldType.Date) {
      return toDateString(fieldValue.value as string, timezone);
    }
    if (type === EExtraFieldType.User) {
      let unitAvatar = null;
      if (fieldValue.groupId) {
        const group = groups.find((groupItem) => groupItem.id === fieldValue.groupId);
        const groupAvatar = {
          ...group,
          type: ETaskPerformerType.UserGroup,
        };
        unitAvatar = groupAvatar;
      } else {
        unitAvatar = getUserById(users, fieldValue.userId);
      }
      return <Avatar user={unitAvatar as TAvatarUser} size="sm" />;
    }
    if (type === EExtraFieldType.Url) {
      return (
        <a href={fieldValue.value as string} target="_blank" rel="noreferrer" className={styles['field-column__url']}>
          {fieldValue.value}
        </a>
      );
    }
    if (type === EExtraFieldType.File) {
      try {
        if (!fieldValue.markdownValue) {
          throw new Error(`getFieldContent(): Empty file markdown value`);
        }

        const filesMap = parseFileListFromMarkdown(fieldValue.markdownValue);
        const fileElements = Array.from(filesMap.entries()).map(([fileName, fileUrl], index, array) =>
          renderFileElement(fileName, fileUrl, index, array),
        );
        return <div className={styles['field-column__files']}>{fileElements}</div>;
      } catch (error) {
        console.error('File processing error:', error);
        return <div className={styles['field-column__files']}>Unable to display file</div>;
      }
    }
    return fieldValue.value;
  };

  return <div className={styles['field-column__content']}>{getFieldContent(value.type, value)}</div>;
}
