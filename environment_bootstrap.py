#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2015 Measurement Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import sys

"""Configure Observatory based on the type of environment this is."""


def create_environment_symlink(link_name, environment_type):
  target_name = '%s.%s' % (os.path.basename(link_name), environment_type)
  print 'Creating symlink %s -> %s' % (link_name, target_name)

  existing_link_removed = False
  if os.path.islink(link_name):
    os.remove(link_name)
    existing_link_removed = True

  os.symlink(target_name, link_name)

  if existing_link_removed:
    print 'Warning: Replaced existing symbolic link: %s' % link_name


def setup_environment(environment_type):
  create_environment_symlink('server/config.py',
                             environment_type)
  create_environment_symlink('server/app.yaml',
                             environment_type)


def main(args):
  setup_environment(args.environment_type)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      prog='mlab-ns Environment Bootstrapper',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('environment_type',
                      choices=['testing', 'live'],
                      help='The type of environment to configure.')
  main(parser.parse_args())

