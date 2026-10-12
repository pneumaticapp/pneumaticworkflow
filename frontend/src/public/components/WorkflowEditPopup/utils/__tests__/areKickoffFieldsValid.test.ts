import { checkExtraFieldsAreValid } from '../areKickoffFieldsValid';
import { makeExtraField } from '../../../../__stubs__/fields.factory';

describe('checkExtraFieldsAreValid', () => {
  it('returns true when fields are undefined or empty', () => {
    expect(checkExtraFieldsAreValid([])).toBe(true);
    expect(checkExtraFieldsAreValid(undefined)).toBe(true);
  });

  it('returns true when all required fields are filled', () => {
    const fields = [
      makeExtraField({ apiName: 'f1', isRequired: true, value: 'text' }),
      makeExtraField({ apiName: 'f2', isRequired: false, value: '' }),
    ];

    expect(checkExtraFieldsAreValid(fields)).toBe(true);
  });

  it('returns false when a visible required field is empty', () => {
    const fields = [
      makeExtraField({ apiName: 'f1', isRequired: true, value: '', isHidden: false }),
    ];

    expect(checkExtraFieldsAreValid(fields)).toBe(false);
  });

  it('returns true when an empty required field is hidden (isHidden: true)', () => {
    const fields = [
      makeExtraField({ apiName: 'f1', isRequired: true, value: '', isHidden: true }),
    ];

    expect(checkExtraFieldsAreValid(fields)).toBe(true);
  });

  it('returns false when both a hidden empty and a visible empty required field are present', () => {
    const fields = [
      makeExtraField({ apiName: 'f-hidden', isRequired: true, value: '', isHidden: true }),
      makeExtraField({ apiName: 'f-visible', isRequired: true, value: '', isHidden: false }),
    ];

    expect(checkExtraFieldsAreValid(fields)).toBe(false);
  });
});
