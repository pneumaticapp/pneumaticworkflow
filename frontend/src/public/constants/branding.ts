import { isRtlLocale } from '../lang/direction';

/** Display identity only; technical service names and API contracts stay stable. */
export const BRAND = {
  name: 'Masarat',
  nameAr: 'مسارات',
  organization: 'Ministry of Public Works and Housing',
  organizationAr: 'وزارة الأشغال العامة والإسكان',
  abbreviation: 'MOPWH',
  homePath: '/',
} as const;

export function getBrandName(locale: string): string {
  return isRtlLocale(locale) ? BRAND.nameAr : BRAND.name;
}

export function getOrganizationName(locale: string): string {
  return isRtlLocale(locale) ? BRAND.organizationAr : BRAND.organization;
}
