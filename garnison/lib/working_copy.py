import json
import os

from fabric.api import local, run, cd

# for TESTING, TODO remove
local = run

class WorkingCopy(object):
    """
    WorkingCopy object handles directory creation, fetching repo,
    checking out correct branches and setting versions before calling
    le-trebuchet for the build
    """
    def __init__(self, name, base_folder="/var/CIC/", repo=None):
        self.name = name
        self.base_folder = base_folder
        self.repo = repo
        self.working_copy = os.path.join(self.base_folder, "working_copy", self.name)

    @property
    def default_missile_path(self):
        return os.path.join(self.working_copy, ".missile.yml")

    def _prepare_folder(self, clean):
        """
        Create/clean the directory for the repo if necessary
        """
        local("test -d %(dir)s || mkdir -p %(dir)s" % {"dir": self.working_copy})
        if clean:
            local("rm -rf %(dir)s/*" % {"dir": self.working_copy})

    def _checkout_working_copy(self, repo, branch):
        """
        Checks out the given branch from the Git repo,
        Returns the long SHA of the branch's HEAD.
        """
        cmd = "test -d %(dir)s/.git || git clone --depth=50 --quiet %(url)s %(dir)s"
        local(cmd % {"dir": self.working_copy, "url": repo})

        with cd(self.working_copy):
            local("git fetch --quiet origin")
            local("git reset --quiet --hard origin/%s" % branch)
            local("git submodule --quiet init")
            local("git submodule --quiet update")
            return local('git rev-parse HEAD')

    def prepare(self, repo=None, branch="master", clean=False):
        repo = repo if repo is not None else self.repo
        assert repo, "Git repository is %(repo)s" % {"repo": repo}
        self._prepare_folder(clean)
        return self._checkout_working_copy(repo, branch)

    def get_current_git_hash(self):
        """
        Return the hash of the current HEAD commit of this working copy.
        """
        with cd(self.working_copy):
            return local("git rev-parse --verify --short HEAD")

    def get_new_git_version(self, prefix="", suffix=""):
        """
        Return commit hash with prefix and suffix
        """
        version = ("%(pre)s-rev%(rev)s-%(suf)s" %
                   {"pre": prefix, "rev": self.get_current_git_hash(), "suf": suffix})
        return version.replace("_", "-")

    def set_version(self, version):
        self.version = version

    def generate_new_base_version(self, old_version):
        """
        Auto-increment the version 
        """
        return str(1 + int(old_version.split("-rev")[0]))

    def _build_version_legacy(self, version):
        """
        compatibility for trebuchet until it gets fixed
        """
        vline = "--app-version %(v)s --env-version %(v)s --service-version %(v)s"
        return vline % {"v": version}

    def build(self, path_to_missile=None, output_path=None):
        """
        Run trebuchet build
        """
        assert self.version, "version not set"
        if path_to_missile is None:
            path_to_missile = self.default_missile_path
        version = self._build_version_legacy(self.version)
        cmd = "trebuchet build %(missile)s --arch amd64 --output %(output)s %(version)s"
        results = local(cmd % {"missile": path_to_missile, "output": output_path,
                               "version": version})
        retval = []
        for pkg in filter(lambda l: l.startswith("Built: "), results.split("\n")):
            retval.append(json.loads("""%s""" % pkg[7:].replace("'", '"')))
        return retval
