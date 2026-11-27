import { getEmptyField } from '../getEmptyField';
import { EExtraFieldType } from '../../../../../types/template';
import { intlMock } from '../../../../../__stubs__/intlMock';

describe('getEmptyField', () => {
  it('creates User field with null userId and groupId', () => {
    const userField = getEmptyField(EExtraFieldType.User, intlMock.formatMessage);

    expect(userField.type).toBe(EExtraFieldType.User);
    expect(userField.userId).toBeNull();
    expect(userField.groupId).toBeNull();
  });
});
