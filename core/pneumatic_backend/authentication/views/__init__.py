from pneumatic_backend.authentication.views.verification import (
    VerificationTokenView,
    VerificationTokenResendView,
)
from pneumatic_backend.authentication.views.password import (
    ChangePasswordView,
    ResetPasswordViewSet,
)
from pneumatic_backend.authentication.views.google import (
    SignInWithGoogleView,
    GoogleAuthViewSet,
)
from pneumatic_backend.authentication.views.signin import (
    TokenObtainPairCustomView,
    SuperuserEmailTokenView,
)
from pneumatic_backend.authentication.views.signup import (
    SignUpView,
)
from pneumatic_backend.authentication.views.context import (
    ContextUserView
)
from pneumatic_backend.authentication.views.signout import (
    SignOutView,
)
from pneumatic_backend.authentication.views.microsoft import (
    MSAuthViewSet
)
from pneumatic_backend.authentication.views.auth0 import (
    Auth0ViewSet
)
