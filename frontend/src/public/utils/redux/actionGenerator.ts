import { ITypedReduxAction } from '../../types/redux';

export function actionGenerator<Type>(type: Type): () => ITypedReduxAction<Type, void>;
export function actionGenerator<Type, Payload>(type: Type): (payload: Payload) => ITypedReduxAction<Type, Payload>;
export function actionGenerator<Type, Payload = void>(type: Type) {
  return (payload?: Payload): ITypedReduxAction<Type, Payload | void> => ({
    type,
    payload,
  });
}
