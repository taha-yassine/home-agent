"""Home Agent REST API."""

from http import HTTPStatus

from homeassistant.components import conversation
from homeassistant.helpers import intent
from homeassistant.helpers import llm
from homeassistant.helpers.http import HomeAssistantView, KEY_HASS
from homeassistant.core import HomeAssistant


def async_register_api_endpoints(hass: HomeAssistant):
    """Register API endpoints."""
    hass.http.register_view(HomeAgentExposedEntitiesApiView())
    hass.http.register_view(HomeAgentEntityStateApiView())


class HomeAgentExposedEntitiesApiView(HomeAssistantView):
    """View to handle Home Agent API requests."""

    url = "/api/home_agent/entities"
    name = "api:home_agent:entities"
    requires_auth = True

    async def get(self, request):
        """Handle GET requests."""
        hass = request.app[KEY_HASS]
        exposed_entities = llm._get_exposed_entities(
            hass,
            conversation.DOMAIN,
            include_state=False,
        )
        return self.json(exposed_entities)


class HomeAgentEntityStateApiView(HomeAssistantView):
    """View to find a single entity and provide its current state."""

    url = "/api/home_agent/entities/state"
    name = "api:home_agent:entities:state"
    requires_auth = True

    async def get(self, request):
        """Handle GET requests to fetch the state of an entity."""
        hass = request.app[KEY_HASS]
        entity_name = request.query.get("name")
        domain = request.query.get("domain")

        if not entity_name:
            return self.json_message(
                "Query parameter 'name' is required.", HTTPStatus.BAD_REQUEST
            )

        domains: set[str] | None = None
        if domain:
            domains = {domain}

        match_constraints = intent.MatchTargetsConstraints(
            name=entity_name,
            domains=domains,
            assistant=conversation.DOMAIN,
        )
        match_preferences = intent.MatchTargetsPreferences()
        match_result = intent.async_match_targets(
            hass, match_constraints, match_preferences
        )

        if not match_result.states:
            return self.json_message("Entity not found", HTTPStatus.NOT_FOUND)

        if len(match_result.states) > 1:
            entity_ids = [s.entity_id for s in match_result.states]
            return self.json(
                {
                    "error": "Multiple entities found. Please be more specific.",
                    "entities": entity_ids,
                },
                status_code=HTTPStatus.CONFLICT,
            )

        state = match_result.states[0]
        return self.json(
            {
                "entity_id": state.entity_id,
                "state": state.state,
                "attributes": state.attributes,
            }
        )
