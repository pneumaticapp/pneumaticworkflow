import { IExtraField } from '../types/template';
import { isArrayWithItems } from '../utils/helpers';
import { deleteAttachment } from './deleteAttachment';

export async function deleteRemovedFilesFromFields(fields?: IExtraField[]) {
  if (!fields) {
    return;
  }

  const filesToDelete = fields.reduce((acc, field) => {
    if (!isArrayWithItems(field.attachments)) {
      return acc;
    }

    const removedFiles = field.attachments.filter(({ isRemoved }) => isRemoved);

    return [...acc, ...removedFiles];
  }, []);

  const deletePromises = filesToDelete.map(file => deleteAttachment(file.id));

  await Promise.all(deletePromises);
}
