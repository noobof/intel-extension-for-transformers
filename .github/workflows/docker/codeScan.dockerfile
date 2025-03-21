#
# Copyright (c) 2022 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG UBUNTU_VER=22.04
FROM ubuntu:${UBUNTU_VER} as devel

# See http://bugs.python.org/issue19846
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    aspell \
    aspell-en \
    python3 \
    python3-pip \
    python3-dev \
    python3-distutils \
    build-essential \
    cloc \
    python3.10-venv \
    git

RUN ln -sf $(which python3) /usr/bin/python

RUN python -m pip install --no-cache-dir pylint==2.12.1\
    bandit==1.7.4\
    pyspelling\
    pydocstyle

WORKDIR /
