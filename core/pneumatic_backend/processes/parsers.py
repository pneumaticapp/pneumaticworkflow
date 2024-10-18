from pneumatic_backend.generics.parsers import CamelCaseJSONParser


class ImportSystemTemplateParser(CamelCaseJSONParser):

    JSON_UNDERSCOREIZE = {
        "no_underscore_before_number": False,
        "ignore_fields": ('kickoff',),
        "ignore_keys": None,
    }
