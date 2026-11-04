export interface IAction<Type> {
  type: Type;
}

export interface ITypedReduxAction<Type, Payload> extends IAction<Type> {
  payload: Payload;
}
