/**
 * Builds the markdown string for an attachment so that Lexical markdown export
 * (which uses DecoratorNode.getTextContent()) and the ATTACHMENT transformer
 * both produce the same format. Backend can persist this and we can re-import it.
 */
export type TAttachmentEntityType = 'image' | 'video' | 'file';

export function buildAttachmentMarkdownString(
  name: string,
  url: string,
  id: number | undefined,
  entityType: TAttachmentEntityType,
): string {
  const idPart = id != null ? `attachment_id:${id} ` : '';
  return `![${name}](${url} "${idPart}entityType:${entityType}")`;
}
