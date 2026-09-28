import { IFieldsetBindingClient } from '../../../types/fieldset';
import { validateFieldsetTitle } from '../../../utils/validators';

export function areFieldsetsValid(fieldsets: IFieldsetBindingClient[] = []): boolean {
  return fieldsets.every((fieldset) => !validateFieldsetTitle(fieldset.title));
}
