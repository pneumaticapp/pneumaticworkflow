export interface IApiOAuthProfileResponse {
  token?: string;
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  phone: string;
  photo: string;
}

export function mapOAuthProfile(data?: Partial<IApiOAuthProfileResponse>) {
  if (!data || (!data.email && !data.token) || !Object.values(data).filter(Boolean).length) {
    return {};
  }
  const { token, email, first_name: firstName, last_name: lastName, company: companyName, phone, photo } = data;
  if (token) {
    return { token };
  }

  return {
    email,
    firstName: firstName || '',
    lastName: lastName || '',
    companyName: companyName || '',
    phone: phone || '',
    photo: photo || '',
  };
}
