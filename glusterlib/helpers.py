#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Nandaja Varma <nvarma@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#    helpers.py
#    ---------
#    Helpers consists of a couple of general helper methods
#    called from various parts of the framework to create directories
#    and run commands
#

import os
import subprocess
import re
import sys
import itertools
import shutil
try:
    import yaml
except ImportError:
    print "Error: Package PyYAML not found."
    sys.exit(0)
from global_vars import Global


class Helpers(Global):

    '''
    Some helper methods to help in directory/file creation/removal etc.
    '''

    def present_in_yaml(self, filename, item):
        doc = self.read_yaml(filename)
        if doc and item in doc:
            return True
        return False

    def get_value_from_yaml(self, filename, item):
        doc = self.read_yaml(filename)
        return doc.get(item)

    def read_yaml(self, filename):
        with open(filename, 'r') as f:
            return yaml.load(f)

    def cleanup_and_quit(self):
        if os.path.isdir(Global.base_dir):
            shutil.rmtree(Global.base_dir)
        sys.exit(0)

    def mk_dir(self, direc):
        if os.path.isdir(direc):
            shutil.rmtree(direc)
        os.makedirs(direc)

    def touch_file(self, filename):
        try:
            os.remove(filename)
        except OSError:
            pass
        os.mknod(filename)

    def copy_files(self, source_dir):
        files = os.listdir(source_dir)
        files_to_move = [self.get_file_dir_path(source_dir, f) for f in files]
        for each in files_to_move:
            try:
                shutil.copy(each, Global.base_dir)
            except IOError as e:
                print "\nError: File copying failed(%s)" % e
                self.cleanup_and_quit()

    def get_file_dir_path(self, basedir, newdir):
        return os.path.join(os.path.realpath(basedir), newdir)

    def uppath(self, path, n):
        # To get the n the parent of a particular directory
        return os.sep.join(path.split(os.sep)[:-n])

    def fix_format_of_values_in_config(self, option_dict, excemption=''):
        '''
        This method will split the values provided in config by user,
        when parsed as a dictionary
        '''
        for key, value in option_dict.iteritems():
            '''
            HACK: The value for option 'transport' can have comma in it,
            eg: tcp,rdma. so comma here doesn't mean that it can have
            multiple values. Hence the excemption argument
            '''
            if ',' in str(value) and key not in [excemption]:
                option_dict[
                    key] = self.split_comma_seperated_options(value)

    def set_default_value_for_dict_key(self, dictname, default_value_dict):
        for key, value in default_value_dict.iteritems():
            if key not in dictname:
                dictname[key] = value

    def check_for_param_presence(self, param, section_dict):
        if param not in section_dict:
            print "Error: %s not provided in the config. " \
                    "Cannot continue!" % param
            self.cleanup_and_quit()

    def split_volname_and_hostname(self, volname):
        '''
        This gives the user the flexibility to not give the hosts
        section. Instead one can just specify the volume name
        with one of the peer member's hostname or IP in the
        format <hostname>:<volumename>
        '''
        if not volname:
            return None
        vol_group = re.search("(.*):(.*)", volname)
        if vol_group:
            if not self.config_section_map(self.config,
                    'volume', 'action', False) == 'add-brick' and (
                            vol_group.group(1) not in Global.hosts):
                Global.hosts.append(vol_group.group(1))
            Global.master = [vol_group.group(1)]
            return vol_group.group(2)
        return volname


    def split_brickname_and_hostname(self, brick):
        if not brick:
            return None
        brk_group = re.search("(.*):(.*)", brick)
        if not brk_group:
            print "\nError: Brick names should be in the format " \
                    "<hostname>:<brickname>. Exiting!"
            self.cleanup_and_quit()
        if brk_group.group(1) not in Global.brick_hosts:
            Global.brick_hosts.append(brk_group.group(1))
        return brk_group.group(2)


    def not_subdir(self, path, directory):
        if path.endswith('/'):
            path = path[:-1]
        base_dir = os.path.abspath(directory)
        is_subdir =  base_dir.startswith(path +
                '/') and base_dir != path
        return not is_subdir


    def exec_ansible_cmd(self, verbose):
        executable = 'ansible-playbook'
        command = [executable, '-i', Global.inventory, verbose,
                Global.playbooks_file]
        command = filter(None, command)
        try:
            subprocess.call(command, shell=False)
        except (OSError, subprocess.CalledProcessError) as e:
            print "Error: Command %s failed. (Reason: %s)" % (cmd, e)
            sys.exit()
