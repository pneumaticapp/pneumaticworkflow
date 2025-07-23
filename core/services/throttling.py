from pneumatic_backend.generics.throttling import (
    AnonThrottle
)


class StepsByDescriptionThrottle(AnonThrottle):

    scope = '04_services__steps_by_description'
