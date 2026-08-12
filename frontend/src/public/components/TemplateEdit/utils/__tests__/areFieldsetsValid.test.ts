import { areFieldsetsValid } from '../areFieldsetsValid';
import { makeFieldsetBindingClient } from '../../../../__stubs__/fieldsets.factory';

describe('areFieldsetsValid', () => {
  it('returns true when all fieldsets have valid titles', () => {
    const fieldsets = [
      makeFieldsetBindingClient({ title: 'Customer Details' }),
      makeFieldsetBindingClient({ title: 'Payment Options' }),
    ];
    expect(areFieldsetsValid(fieldsets)).toBe(true);
  });

  it('returns false when a fieldset has an empty title', () => {
    const fieldsets = [
      makeFieldsetBindingClient({ title: 'Customer Details' }),
      makeFieldsetBindingClient({ title: '' }),
    ];
    expect(areFieldsetsValid(fieldsets)).toBe(false);
  });

  it('returns false when a fieldset title is only whitespace', () => {
    const fieldsets = [
      makeFieldsetBindingClient({ title: '   ' }),
    ];
    expect(areFieldsetsValid(fieldsets)).toBe(false);
  });

  it('returns true for empty fieldsets list', () => {
    expect(areFieldsetsValid([])).toBe(true);
  });
});
