from usaspending_api.awards.models_matviews import SumaryCfdaNumbersView
from usaspending_api.awards.models_matviews import SumaryNaicsCodesView
from usaspending_api.awards.models_matviews import SumaryPscCodesView
from usaspending_api.awards.models_matviews import SummaryAwardView
from usaspending_api.awards.models_matviews import SummaryTransactionView
from usaspending_api.awards.models_matviews import SummaryView
from usaspending_api.common.exceptions import InvalidParameterException
from usaspending_api.awards.v2.filters.location_filter_geocode import geocode_filter_locations
import logging

logger = logging.getLogger(__name__)

MATVIEW_SELECTOR = {
    'SummaryView': {
        'allowed_filters': ['time_period', 'award_type_codes', 'agencies'],
        'model': SummaryView.objects
    },
    'SummaryAwardView': {
        'allowed_filters': ['time_period', 'award_type_codes', 'agencies'],
        'model': SummaryAwardView.objects
    },
    'SumaryPscCodesView': {
        'allowed_filters': ['time_period', 'award_type_codes'],
        'model': SumaryPscCodesView.objects
    },
    'SumaryCfdaNumbersView': {
        'allowed_filters': ['time_period', 'award_type_codes'],
        'model': SumaryCfdaNumbersView.objects
    },
    'SumaryNaicsCodesView': {
        'allowed_filters': ['time_period', 'award_type_codes'],
        'model': SumaryNaicsCodesView.objects
    },
    'SummaryTransactionView': {
        'allowed_filters': [
            'time_period',
            'award_type_codes',
            'legal_entities',
            'recipient_scope',
            'recipient_locations',
            'recipient_type_names',
            'place_of_performance_scope',
            'place_of_performance_locations',
            'naics_codes',
            'psc_codes',
            'contract_pricing_type_codes',
            'set_aside_type_codes',
            'extent_competed_type_codes'],
        'model': SummaryTransactionView.objects
    }
}


def view_filter(filters, view_name):

    try:
        view_objects = MATVIEW_SELECTOR[view_name]['model']
    except Exception:
        raise InvalidParameterException('Invalid view: ' + view_name + ' does not exist.')

    queryset = view_objects.all()

    for key, value in filters.items():
        # check for valid key
        if value is None:
            raise InvalidParameterException('Invalid filter: ' + key + ' has null as its value.')

        # time_period
        if key == "time_period":
            or_queryset = None
            queryset_init = False
            for v in value:
                kwargs = {}
                if v.get("start_date") is not None:
                    kwargs["action_date__gte"] = v.get("start_date")
                if v.get("end_date") is not None:
                    kwargs["action_date__lte"] = v.get("end_date")
                # (may have to cast to date) (oct 1 to sept 30)
                if queryset_init:
                    or_queryset |= view_objects.filter(**kwargs)
                else:
                    queryset_init = True
                    or_queryset = view_objects.filter(**kwargs)
            if queryset_init:
                queryset &= or_queryset

        # award_type_codes
        elif key == "award_type_codes":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(type__in=or_queryset)

        # agencies
        elif key == "agencies":
            or_queryset = None
            funding_toptier = []
            funding_subtier = []
            awarding_toptier = []
            awarding_subtier = []
            for v in value:
                type = v["type"]
                tier = v["tier"]
                name = v["name"]
                if type == "funding":
                    if tier == "toptier":
                        funding_toptier.append(name)
                    elif tier == "subtier":
                        funding_subtier.append(name)
                    else:
                        raise InvalidParameterException('Invalid filter: agencies ' + tier + ' tier is invalid.')
                elif type == "awarding":
                    if tier == "toptier":
                        awarding_toptier.append(name)
                    elif tier == "subtier":
                        awarding_subtier.append(name)
                    else:
                        raise InvalidParameterException('Invalid filter: agencies ' + tier + ' tier is invalid.')
                else:
                    raise InvalidParameterException('Invalid filter: agencies ' + type + ' type is invalid.')
            if len(funding_toptier) != 0:
                queryset &= view_objects.filter(funding_agency_name__in=funding_toptier)
            if len(awarding_toptier) != 0:
                queryset &= view_objects.filter(awarding_agency_name__in=awarding_toptier)

        elif key == "legal_entities":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    recipient_id__in=or_queryset
                )

        # recipient_location_scope (broken till data reload)
        elif key == "recipient_scope":
            if value == "domestic":
                queryset = queryset.filter(
                    recipient_location_country_name="UNITED STATES"
                )
            elif value == "foreign":
                queryset = queryset.exclude(
                    recipient_location_country_name="UNITED STATES"
                )
            else:
                raise InvalidParameterException(
                    'Invalid filter: recipient_scope type is invalid.')

        # recipient_location
        elif key == "recipient_locations":
            or_queryset = geocode_filter_locations(
                'recipient_location', value, 'SummaryTransactionView', True
            )

            queryset &= or_queryset

        # recipient_type_names
        elif key == "recipient_type_names":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    business_categories__overlap=value
                )

        # place_of_performance_scope
        elif key == "place_of_performance_scope":
            if value == "domestic":
                queryset = queryset.filter(pop_country_name="UNITED STATES")
            elif value == "foreign":
                queryset = queryset.exclude(pop_country_name="UNITED STATES")
            else:
                raise InvalidParameterException('Invalid filter: place_of_performance_scope is invalid.')

        # place_of_performance
        elif key == "place_of_performance_locations":
            or_queryset = geocode_filter_locations(
                'pop', value, 'SummaryTransactionView', True
            )
            queryset &= or_queryset

        # award_ids
        elif key == "award_ids":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(award_id__in=or_queryset)

        # program_numbers
        elif key == "program_numbers":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    cfda_number__in=or_queryset)

        # naics_codes
        elif key == "naics_codes":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    naics_code__in=or_queryset)

        # psc_codes
        elif key == "psc_codes":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    psc_code__in=or_queryset)

        # contract_pricing_type_codes
        elif key == "contract_pricing_type_codes":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    type_of_contract_pricing__in=or_queryset)

        # set_aside_type_codes
        elif key == "set_aside_type_codes":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    type_set_aside__in=or_queryset)

        # extent_competed_type_codes
        elif key == "extent_competed_type_codes":
            or_queryset = []
            for v in value:
                or_queryset.append(v)
            if len(or_queryset) != 0:
                queryset &= view_objects.filter(
                    extent_competed__in=or_queryset)
    return queryset


def can_use_view(filters, view_name):
    try:
        key_list = MATVIEW_SELECTOR[view_name]['allowed_filters']
    except KeyError:
        return False

    # Make sure *only* acceptable keys are in the filters for that view_name
    if not set(key_list).issuperset(set(filters.keys())):
        return False

    agencies = filters.get('agencies')
    if agencies:
        for v in agencies:
            if v["tier"] == "subtier":
                return False
    return True
