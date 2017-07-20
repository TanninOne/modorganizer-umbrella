# Copyright (C) 2015 Sebastian Herbord. All rights reserved.
#
# This file is part of Mod Organizer.
#
# Mod Organizer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mod Organizer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mod Organizer.  If not, see <http://www.gnu.org/licenses/>.


from unibuild.builder import Builder
from unibuild.utility.enum import enum
from unibuild.utility.context_objects import on_exit
from subprocess import Popen, PIPE
from config import config
import os.path
import logging
import shutil
import re


class CMake(Builder):

    def __init__(self):
        super(CMake, self).__init__()
        self.__arguments = []
        self.__install = False

    @property
    def name(self):
        if self._context is None:
            return "cmake"
        else:
            return "cmake {0}".format(self._context.name)

    def applies(self, parameters):
        return True

    def fulfilled(self):
        return False

    def arguments(self, arguments):
        self.__arguments = arguments
        return self

    def install(self):
        self.__install = True
        return self

    def process(self, progress):
        if "build_path" not in self._context:
            logging.error("source path not known for {},"
                          " are you missing a matching retrieval script?".format(self._context.name))
            return False

        # prepare for out-of-source build
        build_path = os.path.join(self._context["build_path"], "build")
        #if os.path.exists(build_path):
        #    shutil.rmtree(build_path)
        try:
            os.mkdir(build_path)
        except:
            pass

        soutpath = os.path.join(self._context["build_path"], "stdout.log")
        serrpath = os.path.join(self._context["build_path"], "stderr.log")

        try:
            with on_exit(lambda: progress.finish()):
                with open(soutpath, "w") as sout:
                    with open(serrpath, "w") as serr:
                        proc = Popen(
                            [config["paths"]["cmake"], "-G", "NMake Makefiles", ".."] + self.__arguments,
                            cwd=build_path,
                            env=config["__environment"],
                            stdout=sout, stderr=serr)
                        proc.communicate()
                        if proc.returncode != 0:
                            raise Exception("failed to generate makefile (returncode %s), see %s and %s" %
                                            (proc.returncode, soutpath, serrpath))

                        proc = Popen([config['tools']['make'], "verbose=1"],
                                     shell=True,
                                     env=config["__environment"],
                                     cwd=build_path,
                                     stdout=PIPE, stderr=serr)
                        progress.job = "Compiling"
                        progress.maximum = 100
                        while proc.poll() is None:
                            while True:
                                line = proc.stdout.readline()
                                if line != '':
                                    match = re.search("^\\[([0-9 ][0-9 ][0-9])%\\]", line)
                                    if match is not None:
                                        progress.value = int(match.group(1))
                                    sout.write(line)
                                else:
                                    break

                        if proc.returncode != 0:
                            raise Exception("failed to build (returncode %s), see %s and %s" %
                                            (proc.returncode, soutpath, serrpath))

                        if self.__install:
                            proc = Popen([config['tools']['make'], "install"],
                                         shell=True,
                                         env=config["__environment"],
                                         cwd=build_path,
                                         stdout=sout, stderr=serr)
                            proc.communicate()
                            if proc.returncode != 0:
                                raise Exception("failed to install (returncode %s), see %s and %s" %
                                                (proc.returncode, soutpath, serrpath))
                                return False
        except Exception, e:
            logging.error(e.message)
            return False
        return True


class CMakeEdit(Builder):

    Type = enum(VC=1, CodeBlocks=2)

    def __init__(self, ide_type):
        super(CMakeEdit, self).__init__()
        self.__arguments = []
        self.__type = ide_type

    @property
    def name(self):
        if self._context is None:
            return "cmake edit"
        else:
            return "cmake edit {}".format(self._context.name)

    def applies(self, parameters):
        return True

    def fulfilled(self):
        return False

    def arguments(self, arguments):
        self.__arguments = arguments
        return self

    def __vc_year(self, version):
        if version == "12.0":
            return "2013"
        elif version == "14.0":
            return "2015"

    def __generator_name(self):
        if self.__type == CMakeEdit.Type.VC:
            return "Visual Studio {} {} {}"\
                .format(config['vc_version'].split('.')[0], self.__vc_year(config['vc_version']),"" if config['architecture']=='x86' else "Win64")
        elif self.__type == CMakeEdit.Type.CodeBlocks:
            return "CodeBlocks - NMake Makefiles"

    def prepare(self):
        self._context['edit_path'] = os.path.join(self._context['build_path'], "edit")

    def process(self, progress):
        if "build_path" not in self._context:
            logging.error("source path not known for {},"
                          " are you missing a matching retrieval script?".format(self._context.name))
            return False

        if os.path.exists(self._context['edit_path']):
            shutil.rmtree(self._context['edit_path'])
        os.mkdir(self._context['edit_path'])

        soutpath = os.path.join(self._context["build_path"], "stdout.log")
        serrpath = os.path.join(self._context["build_path"], "stderr.log")

        with open(soutpath, "w") as sout:
            with open(serrpath, "w") as serr:
                proc = Popen(
                    [config["paths"]["cmake"], "-G", self.__generator_name(), ".."] + self.__arguments,
                    cwd=self._context['edit_path'],
                    env=config["__environment"],
                    stdout=sout, stderr=serr)
                proc.communicate()
                if proc.returncode != 0:
                    logging.error("failed to generate makefile (returncode %s), see %s and %s",
                                  proc.returncode, soutpath, serrpath)
                    return False

        return True
