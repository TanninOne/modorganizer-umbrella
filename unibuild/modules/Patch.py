from unibuild.task import Task
from unibuild.utility.lazy import Lazy
import os.path
import shutil


class Replace(Task):

    def __init__(self, filename, search, substitute):
        super(Replace, self).__init__()
        self.__file = filename
        self.__search = search
        self.__substitute = substitute

    @property
    def name(self):
        return "Replace in {}".format(self.__file)

    def process(self, progress):
        full_path = os.path.join(self._context["build_path"], self.__file)
        with open(full_path, "r") as f:
            data = f.read()

        data = data.replace(self.__search, self.__substitute)

        with open(full_path, "w") as f:
            f.write(data)
        return True


class Copy(Task):

    def __init__(self, source, destination):
        super(Copy, self).__init__()
        if isinstance(source, str):
            source = [source]
        self.__source = Lazy(source)
        self.__destination = Lazy(destination)

    @property
    def name(self):
        if self.__source.type() == list:
            return "Copy {}...".format(self.__source()[0])
        else:
            return "Copy {}".format(self.__source.peek())

    def process(self, progress):
        if os.path.isabs(self.__destination()):
            full_destination = self.__destination()
        else:
            full_destination = os.path.join(self._context["build_path"], self.__destination())

        for source in self.__source():
            if not os.path.isabs(source):
                source = os.path.join(self._context["build_path"], source)
            if not os.path.exists(full_destination):
                os.makedirs(full_destination)
            shutil.copy(source, full_destination)
        return True


class CreateFile(Task):
    def __init__(self, filename, content):
        super(CreateFile, self).__init__()
        self.__filename = filename
        self.__content = Lazy(content)

    @property
    def name(self):
        if self._context is not None:
            return "Create File {}-{}".format(self._context.name, self.__filename)
        else:
            return "Create File {}".format(self.__filename)

    def process(self, progress):
        full_path = os.path.join(self._context["build_path"], self.__filename)
        with open(full_path, 'w') as f:
            # the call to str is necessary to ensure a lazy initialised content is evaluated now
            f.write(self.__content())

        return True
