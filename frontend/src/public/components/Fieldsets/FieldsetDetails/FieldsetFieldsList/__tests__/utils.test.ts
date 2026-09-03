import { EExtraFieldType, IExtraField } from '../../../../../types/template';
import { EMoveDirections } from '../../../../../types/workflow';
import { getSortedFields, createField, editField, deleteField, moveField } from '../utils';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../../__stubs__/fields.factory';

jest.mock('../../../../TemplateEdit/KickoffRedux/utils/getEmptyField', () => ({
  getEmptyField: jest.fn((type: string) => ({
    apiName: `new-${type}`,
    name: 'New Field',
    type,
    order: 0,
  })),
}));

jest.mock('../../../../TemplateEdit/ExtraFields/utils/getEditedFields', () => ({
  getEditedFields: jest.fn((fields: IExtraField[], apiName: string, changedProps: Partial<IExtraField>) =>
    fields.map((field) => (field.apiName === apiName ? { ...field, ...changedProps } : field)),
  ),
}));

jest.mock('../../../../../utils/workflows', () => ({
  getNormalizeFieldsOrders: jest.fn((fields: IExtraField[]) =>
    fields.map((field, idx: number) => ({ ...field, order: fields.length - idx })),
  ),
  moveWorkflowField: jest.fn((from: number, to: number, fields: IExtraField[]) => {
    const copy = [...fields];
    const [moved] = copy.splice(from, 1);
    copy.splice(to, 0, moved);
    return copy;
  }),
}));

describe('FieldsetFieldsList/utils', () => {
  const field1 = makeExtraField({ apiName: 'f1', order: 1 });
  const field2 = makeExtraField({ apiName: 'f2', order: 2 });

  describe('getSortedFields', () => {
    it('sorts fields by order in descending order', () => {
      const result = getSortedFields([field1, field2]);
      expect(result[0].apiName).toBe('f2');
      expect(result[1].apiName).toBe('f1');
    });
  });

  describe('createField', () => {
    it('appends empty field and normalizes field orders', () => {
      const result = createField([field1], EExtraFieldType.String, intlMock.formatMessage);
      expect(result).toHaveLength(2);
    });
  });

  describe('editField', () => {
    it('updates specified field properties', () => {
      const result = editField([field1], 'f1', { name: 'Updated' });
      expect(result[0].name).toBe('Updated');
    });
  });

  describe('deleteField', () => {
    it('removes field by apiName and renormalizes orders', () => {
      const result = deleteField([field1, field2], 'f1');
      expect(result).toHaveLength(1);
      expect(result[0].apiName).toBe('f2');
    });
  });

  describe('moveField', () => {
    it('moves field direction Up/Down', () => {
      const result = moveField([field2, field1], 0, EMoveDirections.Down);
      expect(result[0].apiName).toBe('f1');
      expect(result[1].apiName).toBe('f2');
    });
  });
});
