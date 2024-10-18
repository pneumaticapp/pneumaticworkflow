import { people_v1 } from 'googleapis';
import { getFromArray } from '../utils/getFromArray';

export function mapGooglePeopleResponse(data?: people_v1.Schema$Person) {
  if (!data) {
    return {};
  }

  const email: string = getFromArray('value', data.emailAddresses);
  const firstName: string = getFromArray('givenName', data.names);
  const lastName: string = getFromArray('familyName', data.names);
  const companyName = getFromArray('name', data.organizations);
  const phone = getFromArray('value', data.phoneNumbers);
  const photo = getFromArray('url', data.photos);

  return {
    email,
    firstName,
    lastName,
    companyName,
    phone,
    photo,
  };
}
