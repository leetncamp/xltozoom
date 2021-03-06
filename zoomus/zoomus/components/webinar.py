"""Zoom.us REST API Python Client -- Webinar component"""

from __future__ import absolute_import

from zoomus import util
from zoomus.components import base


class WebinarComponent(base.BaseComponent):
    """Component dealing with all webinar related matters"""

    def list(self, **kwargs):
        util.require_keys(kwargs, "host_id")
        if kwargs.get("start_time"):
            kwargs["start_time"] = util.date_to_str(kwargs["start_time"])
        return self.post_request("/webinar/list", params=kwargs)

    def upcoming(self, **kwargs):
        util.require_keys(kwargs, "host_id")
        if kwargs.get("start_time"):
            kwargs["start_time"] = util.date_to_str(kwargs["start_time"])
        return self.post_request("/webinar/list/registration", params=kwargs)

    def create(self, **kwargs):
        util.require_keys(kwargs, ["host_id", "topic"])
        if kwargs.get("start_time"):
            kwargs["start_time"] = util.date_to_str(kwargs["start_time"])
        return self.post_request("/webinar/create", params=kwargs)

    def update(self, **kwargs):
        util.require_keys(kwargs, ["id", "host_id"])
        if kwargs.get("start_time"):
            kwargs["start_time"] = util.date_to_str(kwargs["start_time"])
        return self.post_request("/webinar/update", params=kwargs)

    def delete(self, **kwargs):
        util.require_keys(kwargs, ["id", "host_id"])
        return self.post_request("/webinar/delete", params=kwargs)

    def end(self, **kwargs):
        util.require_keys(kwargs, ["id", "host_id"])
        return self.post_request("/webinar/end", params=kwargs)

    def get(self, **kwargs):
        util.require_keys(kwargs, ["id", "host_id"])
        return self.post_request("/webinar/get", params=kwargs)

    def register(self, **kwargs):
        util.require_keys(kwargs, ["id", "email", "first_name", "last_name"])
        if kwargs.get("start_time"):
            kwargs["start_time"] = util.date_to_str(kwargs["start_time"])
        return self.post_request("/webinar/register", params=kwargs)


class WebinarComponentV2(base.BaseComponent):
    """Component dealing with all webinar related matters"""

    def list(self, **kwargs):
        util.require_keys(kwargs, "user_id")
        return self.get_request(
            "/users/{}/webinars".format(kwargs.get("user_id")), params=kwargs
        )

    def create(self, **kwargs):
        util.require_keys(kwargs, "user_id")
        return self.post_request(
            "/users/{}/webinars".format(kwargs.get("user_id")), params=kwargs
        )

    def update(self, **kwargs):
        util.require_keys(kwargs, "id")
        return self.patch_request(
            "/webinars/{}".format(kwargs.get("id")), params=kwargs
        )

    def delete(self, **kwargs):
        util.require_keys(kwargs, "id")
        return self.delete_request(
            "/webinars/{}".format(kwargs.get("id")), params=kwargs
        )

    def end(self, **kwargs):
        util.require_keys(kwargs, "id")
        return self.put_request(
            "/webinars/{}/status".format(kwargs.get("id")), params={"status": "end"}
        )

    def add_panelists(self, **kwargs):
        """This was added by Lee"""
        util.require_keys(kwargs, "id")
        result = self.post_request(
            "/webinars/{}/panelists".format(kwargs.get('id')), params=kwargs
            )
        return(result)

    def list_panelists(self, **kwargs):
        util.require_keys(kwargs, "id")
        result = self.get_request(
            "/webinars/{}/panelists".format(kwargs.get('id')), params=kwargs
            )
        return(result)
    
    def remove_panelists(self, **kwargs):
        util.require_keys(kwargs, "id")
        result = self.delete_request(
            "/webinars/{}/panelists".format(kwargs.get('id')), params=kwargs
            )
        return(result)
    
    def remove_a_panelist(self, **kwargs):
        util.require_keys(kwargs, "id")
        util.require_keys(kwargs, "panelistid")
        result = self.delete_request(
            "/webinars/{}/panelists/{}".format(kwargs.get('id'), kwargs.get("panelistid")), params=kwargs
            )
        return(result)

    def get(self, **kwargs):
        util.require_keys(kwargs, "id")
        return self.get_request("/webinars/{}".format(kwargs.get("id")), params=kwargs)

    def register(self, **kwargs):
        util.require_keys(kwargs, ["id", "email", "first_name", "last_name"])
        return self.post_request(
            "/webinars/{}/registrants".format(kwargs.get("id")), params=kwargs
        )
