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


def parse_wait_time(wait_time: str):
    hours, minutes, seconds = 0, 0, 0
    wait_time = wait_time.lower()
    if "h" in wait_time:
        hours = int(wait_time.split("h")[0])
        wait_time = wait_time.split("h")[1]
    if "m" in wait_time:
        minutes = int(wait_time.split("m")[0])
        wait_time = wait_time.split("m")[1]
    if "s" in wait_time:
        seconds = int(wait_time.split("s")[0])
    # Convert the hours, minutes, and seconds to total seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds
