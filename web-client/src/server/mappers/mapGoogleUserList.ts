import { admin_directory_v1 } from 'googleapis';
import Schema$Users = admin_directory_v1.Schema$Users;

export function mapGoogleUserList(data?: Schema$Users) {
  if (!data || !data.users) {
    return [];
  }

  return data.users.map(({ primaryEmail: email, name, thumbnailPhotoUrl: avatar, phones }) => {
    return {
      avatar: avatar || '',
      email,
      firstName: (name && name.givenName) || '',
      lastName: (name && name.familyName) || '',
      phone: (phones && phones[0]) || '',
    };
  });
}
