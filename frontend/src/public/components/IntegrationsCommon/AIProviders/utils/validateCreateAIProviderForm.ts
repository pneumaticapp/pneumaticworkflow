import type { IAIProvider, IAIVendor } from '../../../../api/ai/types';
import { getErrorsObject } from '../../../../utils/formik/getErrorsObject';
import { validateRequired } from '../../../../utils/validators';
import { ECreateAIProviderTab } from '../types';
import type { ICreateAIProviderFormValues } from '../types';

const DUPLICATE_NAME_ERROR = 'ai-providers.name-exists';

const normalizeName = (name: string) => name.trim().toLowerCase();

const getDuplicateNameError = (name: string, providers: IAIProvider[]) =>
  name && providers.some((provider) => normalizeName(provider.name) === normalizeName(name))
    ? DUPLICATE_NAME_ERROR
    : '';

export const validateCreateAIProviderForm = (
  values: ICreateAIProviderFormValues,
  tab: ECreateAIProviderTab,
  providers: IAIProvider[],
  vendors: IAIVendor[],
) => {
  if (tab === ECreateAIProviderTab.Vendor) {
    const vendorName = vendors.find(({ slug }) => slug === values.vendor)?.name ?? '';

    return getErrorsObject(values, {
      vendor: (vendor: string) => validateRequired(vendor) || getDuplicateNameError(vendorName, providers),
      apiKey: validateRequired,
    });
  }

  return getErrorsObject(values, {
    name: (name: string) => validateRequired(name) || getDuplicateNameError(name, providers),
    baseUrl: validateRequired,
    apiKey: validateRequired,
  });
};
