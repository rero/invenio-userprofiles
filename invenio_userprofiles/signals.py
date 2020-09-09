# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signals for for user profiles."""

from blinker import Namespace

_signals = Namespace()

after_profile_update = _signals.signal('before-record-insert')
"""Signal is sent after a profile is updated."""
