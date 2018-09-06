# Copyright (C) 2018 Arrai Innovations Inc. - All Rights Reserved
import os
import subprocess
import venv
import sys
from tempfile import TemporaryDirectory, NamedTemporaryFile
from unittest import TestCase

from colors import color


class ExtraneousTestCase(TestCase):
    cwd_path = ''
    env_path = ''
    _cwd_path = TemporaryDirectory()
    _env_path = TemporaryDirectory()

    @classmethod
    def setUpClass(cls):
        cls.cwd_path = cls._cwd_path.__enter__()
        cls.env_path = cls._env_path.__enter__()
        cls.setup_venv()

    @classmethod
    def tearDownClass(cls):
        cls._env_path.__exit__(None, None, None)
        cls._cwd_path.__exit__(None, None, None)

    @staticmethod
    def subcmd(cmd, cwd_path=None):
        kwargs = {
            'shell': True, 'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'check': False
        }
        if cwd_path:
            kwargs['cwd'] = cwd_path
        ran = subprocess.run(cmd, **kwargs)
        try:
            ran.check_returncode()
        except subprocess.CalledProcessError as e:
            print('stdout', ran.stdout)
            print('stderr', ran.stderr)
            raise
        return ran

    @classmethod
    def pip_install(cls, package, editable=False, upgrade=False):
        return cls.subcmd(
            '{env_path}/bin/python -m pip install {upgrade}{editable}{package}'.format(
                env_path=cls.env_path,
                upgrade='--upgrade ' if upgrade else '',
                editable='-e ' if editable else '',
                package=package
            )
        )

    @classmethod
    def setup_venv(cls, editable=False):
        real_cwd = os.getcwd()
        venv.create(cls.env_path, with_pip=True)
        cls.pip_install('pip setuptools', upgrade=True)
        cls.pip_install(real_cwd, editable=True)
        for package in [
            'extraneous_sub_package_1',
            'extraneous_sub_package_2',
            'extraneous_top_package_1',
            'extraneous_top_package_2',
            'extraneous_top_package_3',
        ]:
            pkg_name = '{}/test_packages/{}'.format(real_cwd, package)
            cls.pip_install(pkg_name, editable=editable)
        with open('{cwd_path}/requirements.txt'.format(cwd_path=cls.cwd_path), mode='w') as w:
            w.write('extraneous-top-package-1\n')
        with open('{cwd_path}/test_requirements.txt'.format(cwd_path=cls.cwd_path), mode='w') as w:
            w.write('extraneous-top-package-3\n')

    @classmethod
    def get_sitepackages_for_venv(cls):
        ran = cls.subcmd(
            '{env_path}/bin/python -c "from site import getsitepackages; import os;'
            'print(\'\\n\\t\'.join([os.path.relpath(x, os.getcwd()) for x in getsitepackages()]))"'.format(
                env_path=cls.env_path
            ),
            cwd_path=cls.cwd_path
        )
        return ran.stdout.decode('utf8').strip()

    def test_verbose(self):
        extraneous = self.subcmd(
            '{env_path}/bin/extraneous.py -v'.format(env_path=self.env_path),
            cwd_path=self.cwd_path
        )
        self.assertMultiLineEqual(
            'reading installed from:\n\t{site_packages}\n'
            'reading requirements from:\n\t{requirements}\n'
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                site_packages=self.get_sitepackages_for_venv(),
                requirements='\n\t'.join([
                    'requirements.txt',
                    'local_requirements.txt (Not Found)',
                    'test_requirements.txt'
                ]),
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2',
                }) + sorted({
                    'extraneous-sub-package-2',
                })),
            ),
            extraneous.stdout.decode('utf8')
        )

    def test_full(self):
        extraneous = self.subcmd(
            '{env_path}/bin/extraneous.py -f'.format(env_path=self.env_path),
            cwd_path=self.cwd_path
        )
        self.assertMultiLineEqual(
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2', 'extraneous'
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2', 'extraneous'
                }) + sorted({
                    'extraneous-sub-package-2', 'ansicolors', 'pipdeptree'
                })),
            ),
            extraneous.stdout.decode('utf8')
        )

    def test_exclude_top(self):
        extraneous = self.subcmd(
            '{env_path}/bin/extraneous.py -e extraneous-top-package-2'.format(env_path=self.env_path),
            cwd_path=self.cwd_path
        )
        self.assertMultiLineEqual(
            '',
            extraneous.stdout.decode('utf8')
        )

    def test_exclude_sub(self):
        extraneous = self.subcmd(
            '{env_path}/bin/extraneous.py -e extraneous-sub-package-2'.format(env_path=self.env_path),
            cwd_path=self.cwd_path
        )
        self.assertMultiLineEqual(
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                }) + sorted({
                    'extraneous-top-package-2'
                })),
            ),
            extraneous.stdout.decode('utf8')
        )

    def test_include(self):
        other_req = NamedTemporaryFile(mode='w+', delete=False)
        other_req.write('extraneous-top-package-2\n')
        other_req.close()
        try:
            extraneous = self.subcmd(
                '{env_path}/bin/extraneous.py -v -i {other_req}'.format(
                    env_path=self.env_path, other_req=other_req.name
                ),
                cwd_path=self.cwd_path
            )
            self.assertMultiLineEqual(
                'reading installed from:\n\t{site_packages}\n'
                'reading requirements from:\n\t{requirements}\n'
                '{extraneous}\n'
                'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                    site_packages=self.get_sitepackages_for_venv(),
                    requirements='\n\t'.join([
                        other_req.name
                    ]),
                    extraneous=color(
                        'extraneous packages:\n\t{}'.format(' '.join(sorted({
                            'extraneous-top-package-1', 'extraneous-top-package-3',
                        }))),
                        fg='yellow'
                    ),
                    uninstall=' '.join(sorted({
                        'extraneous-top-package-1', 'extraneous-top-package-3',
                    })),
                ),
                extraneous.stdout.decode('utf8')
            )
        finally:
            os.unlink(other_req.name)

    def test_installed_editable(self):
        # todo: implement
        pass
