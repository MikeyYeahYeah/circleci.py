# -*- coding: utf-8 -*-
"""
CircleCI API Module

:copyright: (c) 2017 by Lev Lazinskiy
:license: MIT, see LICENSE for more details.
"""
import requests
from requests.auth import HTTPBasicAuth

from circleci.error import BadKeyError, BadVerbError, InvalidFilterError


class Api():
    """A python interface into the CircleCI API"""

    def __init__(self, token, url='https://circleci.com/api/v1.1'):
        """Instantiate a new circleci.Api object.

        Args:
            url (str):
                The URL to the CircleCI instance
                defaults to https://circleci.com/api/v1.1

                If you are running CircleCI server, the API
                is available at the same endpoint of your own
                installation url. i.e (https://circleci.yourcompany.com/api/v1.1)

            token (str):
                Your CircleCI token.abs
        """
        self.token = token
        self.url = url

    def get_user_info(self):
        """Provides information about the signed in user.

        Endpoint:
            GET: /me
        """
        resp = self._request('GET', 'me')
        return resp

    def get_projects(self):
        """List of all the projects you're following on CircleCI.

        Endpoint:
            GET: /projects
        """
        resp = self._request('GET', 'projects')
        return resp

    def follow_project(self, username, project, vcs_type='github'):
        """Follow a new project on CircleCI.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/follow
        """
        endpoint = 'project/{0}/{1}/{2}/follow'.format(
            vcs_type,
            username,
            project
        )
        resp = self._request('POST', endpoint)
        return resp

    def get_project_build_summary(
            self,
            username,
            project,
            limit=30,
            offset=0,
            status_filter=None,
            branch=None,
            vcs_type='github'):
        """Build summary for each of the last 30 builds for a single git repo.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            limit (int) (optional):
                The number of builds to return. Maximum 100, defaults to 30.
            offset (int) (optional):
                The API returns builds starting from this offset, defaults to 0.
            status_filter (str) (optional):
                Restricts which builds are returned. Set to "completed", "successful",
                "failed", "running", or defaults to no filter.
            branch (str) (optional):
                Narrow returned builds to a single branch.
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Raise:
            InvalidFilterError

        Endpoint:
            GET: /project/:vcs-type/:username/:project
        """
        valid_filters = [None, 'completed', 'successful', 'failed', 'running']

        if status_filter not in valid_filters:
            raise InvalidFilterError(status_filter, 'status')

        if branch:
            endpoint = 'project/{0}/{1}/{2}/tree/{3}?limit={4}&offset={5}&filter={6}'.format(
                vcs_type,
                username,
                project,
                branch,
                limit,
                offset,
                status_filter
            )
        else:
            endpoint = 'project/{0}/{1}/{2}?limit={3}&offset={4}&filter={5}'.format(
                vcs_type,
                username,
                project,
                limit,
                offset,
                status_filter
            )

        resp = self._request('GET', endpoint)
        return resp

    def get_recent_builds(self, limit=30, offset=0):
        """
        Build summary for each of the last 30 recent builds, ordered by build_num.

        Args:
            limit (int) (optional):
                The number of builds to return. Maximum 100, defaults to 30.
            offset (int) (optional):
                The API returns builds starting from this offset, defaults to 0.
        Endpoint:
            GET: /recent-builds
        """
        endpoint = 'recent-builds?limit={0}&offset={1}'.format(limit, offset)

        resp = self._request('GET', endpoint)
        return resp

    def get_build_info(self, username, project, build_num, vcs_type='github'):
        """Full details for a single build.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            build_num (str):
                build number
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET: /project/:vcs-type/:username/:project/:build_num
        """
        endpoint = 'project/{0}/{1}/{2}/{3}'.format(
            vcs_type,
            username,
            project,
            build_num
        )
        resp = self._request('GET', endpoint)
        return resp

    def get_artifacts(self, username, project, build_num, vcs_type='github'):
        """List the artifacts produced by a given build.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            build_num (str):
                build number
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET: /project/:vcs-type/:username/:project/:build_num/artifacts
        """
        endpoint = 'project/{0}/{1}/{2}/{3}/artifacts'.format(
            vcs_type,
            username,
            project,
            build_num
        )
        resp = self._request('GET', endpoint)
        return resp

    def get_latest_artifact(
            self,
            username,
            project,
            branch=None,
            status_filter='completed',
            vcs_type='github'):
        """List the artifacts produced by the latest build on a given branch.

        This endpoint is a little bit flakey. If the "latest" build does not have any artifacts,
        rathern than returning an empty set, the API will 404.

        Args:
            username: org or user name
            project: case sensitive repo name
            branch: The branch you would like to look in for the latest build.
                Returns artifacts for latest build in entire project if omitted.
            filter: Restricts which builds are returned.
                defaults to 'completed'
                valid filters: "completed", "successful", "failed"
            vcs_type: defaults to github
                on circleci.com you can also pass in bitbucket

        Raises:
            InvalidFilterError

        Endpoint:
            GET: /project/:vcs-type/:username/:project/latest/artifacts
        """
        valid_filters = ['completed', 'successful', 'failed']

        if status_filter not in valid_filters:
            raise InvalidFilterError(status_filter, 'artifacts')

        # passing None makes the API 404
        if branch:
            endpoint = 'project/{0}/{1}/{2}/latest/artifacts?branch={3}&filter={4}'.format(
                vcs_type,
                username,
                project,
                branch,
                status_filter
            )
        else:
            endpoint = 'project/{0}/{1}/{2}/latest/artifacts?filter={3}'.format(
                vcs_type,
                username,
                project,
                status_filter
            )

        resp = self._request('GET', endpoint)
        return resp

    def retry_build(self, username, project, build_num, ssh=False, vcs_type='github'):
        """Retries the build.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            build_num (str):
                build number
            ssh: retry a build with SSH enabled
                defaults to False
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/:build_num/retry
        """
        if ssh:
            endpoint = 'project/{0}/{1}/{2}/{3}/ssh'.format(
                vcs_type,
                username,
                project,
                build_num
            )
        else:
            endpoint = 'project/{0}/{1}/{2}/{3}/retry'.format(
                vcs_type,
                username,
                project,
                build_num
            )
        resp = self._request('POST', endpoint)
        return resp

    def cancel_build(self, username, project, build_num, vcs_type='github'):
        """Cancels the build.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            build_num (str):
                build number
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/:build_num/cancel
        """
        endpoint = 'project/{0}/{1}/{2}/{3}/cancel'.format(
            vcs_type,
            username,
            project,
            build_num
        )
        resp = self._request('POST', endpoint)
        return resp

    def add_ssh_user(self, username, project, build_num, vcs_type='github'):
        """Adds a user to the build's SSH permissions.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            build_num (str):
                build number
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/:build_num/ssh-users
        """
        endpoint = 'project/{0}/{1}/{2}/{3}/ssh-users'.format(
            vcs_type,
            username,
            project,
            build_num
        )
        resp = self._request('POST', endpoint)
        return resp


    def trigger_build(
            self,
            username,
            project,
            branch='master',
            revision=None,
            tag=None,
            parallel=None,
            params=None,
            vcs_type='github'):
        """
        Triggers a new build.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            branch (str):
                defaults to master
            revision: specific revision to build
                Default is null and the head of the branch is used.
                Cannot be used with tag parameter.
            tag: The tag to build.
                Default is null.
                Cannot be used with revision parameter.
            parallel: The number of containers to use to run the build.
                Default is null and the project default is used.
                This parameter is ignored for builds running on our 2.0 infrastructure.
            params (dict):
                optional build parameters
                https://circleci.com/docs/1.0/parameterized-builds/
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/tree/:branch
        """
        data = {
            'revision': revision,
            'tag': tag,
            'parallel': parallel,
        }

        if params:
            data.update(params)

        endpoint = 'project/{0}/{1}/{2}/tree/{3}'.format(
            vcs_type,
            username,
            project,
            branch
        )

        resp = self._request('POST', endpoint, data=data)
        return resp

    def add_ssh_key(
            self,
            username,
            project,
            ssh_key,
            vcs_type='github',
            hostname=None):
        """Create an ssh key

        Used to access external systems that require SSH key-based authentication.

        Params:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            branch (str):
                defaults to master
            ssh_key(str):
                private rsa key

                note: this must be unencrypted
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket
            hostname (str):
                optional hostname, if set the key
                will only work for this hostname.

        Endpoint:
            POST: /project/:vcs-type/:username/:project/ssh-key
        """
        endpoint = 'project/{0}/{1}/{2}/ssh-key'.format(
            vcs_type,
            username,
            project
        )

        params = {
            "hostname": hostname,
            "private_key": ssh_key
        }

        resp = self._request('POST', endpoint, data=params)
        return resp

    def list_checkout_keys(self, username, project, vcs_type='github'):
        """List checkout keys for a project

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET: /project/:vcs-type/:username/:project/checkout-key
        """
        endpoint = 'project/{0}/{1}/{2}/checkout-key'.format(
            vcs_type,
            username,
            project
        )

        resp = self._request('GET', endpoint)
        return resp

    def create_checkout_key(self, username, project, key_type, vcs_type='github'):
        """Create a new checkout keys for a project

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            key_type (str):
                The type of key to create

                Can be 'deploy-key' or 'github-user-key'
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/checkout-key
        """
        valid_types = ['deploy-key', 'github-user-key']

        if key_type not in valid_types:
            raise BadKeyError(key_type)

        params = {
            "type": key_type
        }

        endpoint = 'project/{0}/{1}/{2}/checkout-key'.format(
            vcs_type,
            username,
            project
        )

        resp = self._request('POST', endpoint, data=params)
        return resp

    def get_checkout_key(self, username, project, fingerprint, vcs_type='github'):
        """Get a checkout key.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            fingerprint (str):
                The fingerprint of the checkout key
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET: /project/:vcs-type/:username/:project/checkout-key/:fingerprint
        """
        endpoint = 'project/{0}/{1}/{2}/checkout-key/{3}'.format(
            vcs_type,
            username,
            project,
            fingerprint
        )

        resp = self._request('GET', endpoint)

        return resp

    def delete_checkout_key(self, username, project, fingerprint, vcs_type='github'):
        """Delete a checkout key.

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            fingerprint (str):
                The fingerprint of the checkout key
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            DELETE: /project/:vcs-type/:username/:project/checkout-key/:fingerprint
        """
        endpoint = 'project/{0}/{1}/{2}/checkout-key/{3}'.format(
            vcs_type,
            username,
            project,
            fingerprint
        )

        resp = self._request('DELETE', endpoint)
        return resp

    def clear_cache(self, username, project, vcs_type='github'):
        """Clear cache for a project

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            DELETE: /project/:vcs-type/:username/:project/build-cache
        """
        endpoint = 'project/{0}/{1}/{2}/build-cache'.format(
            vcs_type,
            username,
            project
        )
        resp = self._request('DELETE', endpoint)
        return resp

    def add_heroku_key(self, apikey):
        """Adds your Heroku API key to CircleCI

        Args:
            apikey: Heroku API Key

        Endpoint:
            POST: /user/heroku-key
        """
        params = {
            "apikey": apikey
        }

        resp = self._request('POST', 'user/heroku-key', data=params)
        return resp

    def get_test_metadata(self, username, project, build_num, vcs_type='github'):
        """Provides test metadata for a build

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            build_num (str):
                build number
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET: /project/:vcs-type/:username/:project/:build_num/tests
        """
        endpoint = 'project/{0}/{1}/{2}/{3}/tests'.format(
            vcs_type,
            username,
            project,
            build_num
        )

        resp = self._request('GET', endpoint)
        return resp

    def list_envvars(self, username, project, vcs_type='github'):
        """Provides list of environment variables for a project

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET: /project/:vcs-type/:username/:project/envvar
        """
        endpoint = 'project/{0}/{1}/{2}/envvar'.format(
            vcs_type,
            username,
            project
        )

        resp = self._request('GET', endpoint)
        return resp

    def add_envvar(self, username, project, name, value, vcs_type='github'):
        """Adds an environment variable to a project

        Args:
            username (str):
                org or user name
            project (str):
                case sensitive repo name
            name: name of the envvar
            value: value of the envvar
            vcs_type (str):
                defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            POST: /project/:vcs-type/:username/:project/envvar
        """
        params = {
            "name": name,
            "value": value
        }

        endpoint = 'project/{0}/{1}/{2}/envvar'.format(
            vcs_type,
            username,
            project
        )

        resp = self._request('POST', endpoint, data=params)
        return resp

    def get_envvar(self, username, project, name, vcs_type='github'):
        """Gets the hidden value of an environment variable

        Args:
            username: org or user name
            project: case sensitive repo name
            name: name of the envvar
            vcs_type: defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            GET /project/:vcs-type/:username/:project/envvar/:name
        """
        endpoint = 'project/{0}/{1}/{2}/envvar/{3}'.format(
            vcs_type,
            username,
            project,
            name
        )

        resp = self._request('GET', endpoint)

        return resp

    def delete_envvar(self, username, project, name, vcs_type='github'):
        """Delete an environment variable

        Args:
            username: org or user name
            project: case sensitive repo name
            name: name of the envvar
            vcs_type: defaults to github
                on circleci.com you can also pass in bitbucket

        Endpoint:
            DELETE /project/:vcs-type/:username/:project/envvar/:name
        """
        endpoint = 'project/{0}/{1}/{2}/envvar/{3}'.format(
            vcs_type,
            username,
            project,
            name
        )

        resp = self._request('DELETE', endpoint)

        return resp

    def _request(self, verb, endpoint, data=None):
        """Request a url.

        Args:
            endpoint (str):
                The api endpoint we want to call
            verb (str):
                POST or GET
            params (dict):
                optional build parameters

        Raises:
            requests.exceptions.HTTPError

        Returns:
            A JSON object with the response from the API
        """

        headers = {
            'Accept': 'application/json',
        }
        auth = HTTPBasicAuth(self.token, '')
        resp = None

        request_url = "{0}/{1}".format(self.url, endpoint)

        if verb == 'GET':
            resp = requests.get(request_url, auth=auth, headers=headers)
        elif verb == 'POST':
            resp = requests.post(request_url, auth=auth, headers=headers, data=data)
        elif verb == 'DELETE':
            resp = requests.delete(request_url, auth=auth, headers=headers)
        else:
            raise BadVerbError(verb)

        resp.raise_for_status()

        return resp.json()
