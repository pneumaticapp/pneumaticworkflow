from typing import Dict, List


class TemplateRulesetsMixin:

    """ Sync rulesets on a field or fieldset template. """

    ruleset_service_class = None
    ruleset_exception_class = None
    parent_service_exception = None
    parent_id_field = None

    def create_ruleset(self, ruleset_data: dict):
        service = self.ruleset_service_class(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        try:
            return service.create(
                **{self.parent_id_field: self.instance.id},
                template_id=self.instance.template_id,
                **ruleset_data,
            )
        except self.ruleset_exception_class as ex:
            raise self.parent_service_exception(message=ex.message) from ex

    def create_rulesets(self, rulesets_data: List[Dict]):
        for ruleset_data in rulesets_data:
            self.create_ruleset(ruleset_data)

    def update_rulesets(self, rulesets_data: List[Dict]):
        existing_rulesets = {
            ruleset.api_name: ruleset
            for ruleset in self.instance.rulesets.all()
        }
        ruleset_api_names = set()
        for ruleset_data in rulesets_data:
            ruleset_api_name = ruleset_data.get('api_name')
            if ruleset_api_name and ruleset_api_name in existing_rulesets:
                service = self.ruleset_service_class(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_rulesets[ruleset_api_name],
                )
                service.partial_update(**ruleset_data)
                ruleset_api_names.add(ruleset_api_name)
            else:
                ruleset = self.create_ruleset(ruleset_data)
                ruleset_api_names.add(ruleset.api_name)
        self.instance.rulesets.exclude(
            api_name__in=ruleset_api_names,
        ).delete()


class RuleGroupsSyncMixin:

    """ Sync OR/AND groups. Create/update hooks stay on the service. """

    def _set_groups_and(self, group_or, groups_and_data: List[Dict]):
        existing_groups_and = {
            group_and.api_name: group_and
            for group_and in group_or.groups_and.all()
        }
        groups_and_api_names = set()
        for group_and_data in groups_and_data:
            api_name = group_and_data.get('api_name')
            if api_name and api_name in existing_groups_and:
                group_and = self._update_group_and(
                    group_and=existing_groups_and[api_name],
                    group_and_data=group_and_data,
                )
            else:
                group_and = self._create_group_and(
                    group_or=group_or,
                    group_and_data=group_and_data,
                )
            groups_and_api_names.add(group_and.api_name)
        group_or.groups_and.exclude(
            api_name__in=groups_and_api_names,
        ).delete()

    def _set_groups_or(self, groups_or_data: List[Dict]):
        existing_groups_or = {
            group_or.api_name: group_or
            for group_or in self.instance.groups_or.all()
        }
        groups_or_api_names = set()
        for group_or_data in groups_or_data:
            api_name = group_or_data.get('api_name')
            if api_name and api_name in existing_groups_or:
                group_or = self._update_group_or(
                    group_or=existing_groups_or[api_name],
                    group_or_data=group_or_data,
                )
            else:
                group_or = self._create_group_or(
                    group_or_data=group_or_data,
                )
            groups_or_api_names.add(group_or.api_name)
        self.instance.groups_or.exclude(
            api_name__in=groups_or_api_names,
        ).delete()
