export const enum EOAuthType {
  Google = 'Google',
  Microsoft = 'Microsoft',
  SSOAuth0 = 'SSOAuth0',
  SSOOkta = 'SSOOkta',
}

export const enum ERegisterType {
  Common = 'Common',
}

export type TRegisterType = EOAuthType | ERegisterType;
