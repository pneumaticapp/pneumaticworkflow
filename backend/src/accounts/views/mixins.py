from django.contrib.auth import get_user_model

from src.accounts.messages import MSG_A_0052
from src.accounts.serializers.user import (
    UserSerializer,
    VacationActivateSerializer,
)
from src.accounts.services.vacation import (
    VacationDelegationService,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class VacationViewMixin:
    """Shared vacation activate/deactivate logic for views."""

    def _activate_vacation(self, request, user):
        slz = VacationActivateSerializer(
            data=request.data,
            context={
                **self.get_serializer_context(),
                'vacation_user': user,
            },
        )
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        service = VacationDelegationService(user=user)
        service.activate(
            substitute_user_ids=data['substitute_user_ids'],
            absence_status=data['absence_status'],
            vacation_start_date=(
                data.get('vacation_start_date')
            ),
            vacation_end_date=(
                data.get('vacation_end_date')
            ),
        )
        user.refresh_from_db()
        return self.response_ok(
            UserSerializer(instance=user).data,
        )

    def _deactivate_vacation(self, user):
        if not user.is_absent:
            raise_validation_error(
                message=MSG_A_0052,
            )
        service = VacationDelegationService(user=user)
        service.deactivate()
        user.refresh_from_db()
        return self.response_ok(
            UserSerializer(instance=user).data,
        )
