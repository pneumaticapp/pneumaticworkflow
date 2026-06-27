import { IFieldsetBinding, IFieldsetBindingClient } from '../types/fieldset';

export function mapFieldsetBindingsToClient(fieldsets: IFieldsetBinding[]): IFieldsetBindingClient[] {
  return fieldsets.map(({ apiName, ...rest }) => ({
    ...rest,
    apiNameBinding: apiName,
  }));
}
