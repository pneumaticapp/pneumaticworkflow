import { IFieldsetBinding, IFieldsetBindingClient, IFieldsetTaskAPI, IFieldsetRuntime } from '../types/fieldset';

export function mapFieldsetBindingsToClient(fieldsets: IFieldsetBinding[]): IFieldsetBindingClient[] {
  return fieldsets.map(({ apiName, ...rest }) => ({
    ...rest,
    apiNameBinding: apiName,
  }));
}

export function mapFieldsetTaskAPIToRuntime(fieldsets: IFieldsetTaskAPI[]): IFieldsetRuntime[] {
  return fieldsets.map(({ id, apiName, ...rest }) => ({
    ...rest,
    apiNameBinding: apiName,
  }));
}
