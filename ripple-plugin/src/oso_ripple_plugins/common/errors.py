# Copyright (c) 2025 IBM Corp.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class ConfigError(Exception):
    """Exception raised when an Environment Variable is not found"""

    pass


class NetworkError(Exception):
    """Raised for network-level failures (timeout, connection error)"""

    pass


class AuthenticationError(Exception):
    """Raised when the token endpoint returns 401 or 403"""

    pass


class TokenError(Exception):
    """Raised when a token cannot be obtained or parsed from the response"""

    pass
