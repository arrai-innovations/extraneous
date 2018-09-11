# Copyright (C) 2018 Arrai Innovations Inc. - All Rights Reserved
import json
import os
import subprocess
import venv
from tempfile import TemporaryDirectory
from unittest import TestCase

from colors import color


class ExtraneousTestCase(TestCase):
    maxDiff = None
    cwd_path = ''
    env_path = ''
    _cwd_path = TemporaryDirectory()
    _env_path = TemporaryDirectory()
    test_packages = [
        'extraneous_sub_sub_package_1',
        'extraneous_sub_sub_package_2',
        'extraneous_sub_package_1',
        'extraneous_sub_package_2',
        'extraneous_sub_package_3',
        'extraneous_top_package_1',
        'extraneous_top_package_2',
        'extraneous_top_package_3',
        'extraneous_top_package_4',
    ]

    @classmethod
    def setUpClass(cls):
        cls.cwd_path = cls._cwd_path.__enter__()
        cls.env_path = cls._env_path.__enter__()
        cls.setup_venv()
        cls.subcmd('coverage erase', cwd_path=os.getcwd(), parent_envs=True)

    @classmethod
    def tearDownClass(cls):
        cls.subcmd('cp {cwd_path}/.coverage.* {real_cwd}/'.format(cwd_path=cls.cwd_path, real_cwd=os.getcwd()))
        cls.subcmd('coverage combine', cwd_path=os.getcwd(), parent_envs=True)
        try:
            cls.subcmd('rm -rf htmlcov', cwd_path=os.getcwd(), parent_envs=True)
        except subprocess.CalledProcessError:
            pass
        cls.subcmd('coverage html', cwd_path=os.getcwd(), parent_envs=True)
        cls._env_path.__exit__(None, None, None)
        cls._cwd_path.__exit__(None, None, None)

    @classmethod
    def subcmd(cls, cmd, cwd_path=None, coverage=False, parent_envs=False):
        kwargs = {
            'shell': True,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'check': False,
            'cwd': cls.cwd_path if not cwd_path else cwd_path
        }
        if not parent_envs:
            kwargs['env'] = cls.env_vars
        if coverage:
            cmd = 'coverage run -p ' + cmd
        ran = subprocess.run(cmd, **kwargs)
        try:
            ran.check_returncode()
        except subprocess.CalledProcessError as e:
            if ran.stdout:
                print('stdout', ran.stdout)
            if ran.stderr:
                print('stderr', ran.stderr)
            raise
        return ran

    @classmethod
    def pip_install(cls, package, editable=False, upgrade=False):
        return cls.subcmd(
            'python -m pip install {upgrade}{editable}{package}'.format(
                env_path=cls.env_path,
                upgrade='--upgrade ' if upgrade else '',
                editable='-e ' if editable else '',
                package=package
            )
        )

    @classmethod
    def setup_venv(cls):
        real_cwd = os.getcwd()
        venv.create(cls.env_path, with_pip=True, symlinks=True)
        cls.env_vars = {
            'PATH': '{}/bin:'.format(cls.env_path) + os.environ.get('PATH'),
            'VIRTUAL_ENV': cls.env_path,
        }
        cls.pip_install('pip setuptools coverage', upgrade=True)
        cls.pip_install(real_cwd, editable=True)
        echo = 'echo "import coverage; coverage.process_startup()"'
        pth_path = 'import sys; print(' \
                   '[x for x in sys.path if \'site-packages\' in x][0] + \'/coverage-all-the-things.pth\'' \
                   ')'
        pth_wrap = 'python -c "{pth_path}"'.format(env_path=cls.env_path, pth_path=pth_path)
        cls.subcmd('{echo} > `{pth_wrap}`'.format(echo=echo, pth_wrap=pth_wrap))
        cls.pip_install(' '.join('{}/test_packages/{}'.format(real_cwd, package) for package in cls.test_packages))
        with open('{cwd_path}/requirements.txt'.format(cwd_path=cls.cwd_path), mode='w') as w:
            w.write('extraneous-top-package-1\n')
        with open('{cwd_path}/test_requirements.txt'.format(cwd_path=cls.cwd_path), mode='w') as w:
            w.write('extraneous-top-package-3\ncoverage\n')
        with open('{cwd_path}/.coveragerc'.format(cwd_path=cls.cwd_path), mode='w') as w:
            w.write('''[run]
branch = True
parallel = True
concurrency = multiprocessing
include = *extraneous/extraneous.py

[report]
exclude_lines =
    raise NotImplementedError
    except ImportError'''.format(env_path=cls.env_path))

    @classmethod
    def get_sitepackages_for_venv(cls, cwd_path=None):
        ran = cls.subcmd(
            'python -c "from site import getsitepackages; import os;'
            'print(\'\\n\\t\'.join([os.path.relpath(x, os.getcwd()) for x in getsitepackages()]))"'.format(
                env_path=cls.env_path
            ),
            cwd_path=cwd_path
        )
        return ran.stdout.decode('utf8').strip()

    def test_verbose(self):
        extraneous = self.subcmd(
            '`which extraneous.py` -v',
            coverage=True
        )
        self.assertMultiLineEqual(
            'reading installed from:\n\t{site_packages}\n'
            'reading requirements from:\n\t{requirements}\n'
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                site_packages=self.get_sitepackages_for_venv(),
                requirements='\n\t'.join([
                    'requirements.txt',
                    'test_requirements.txt'
                ]),
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                        'extraneous-top-package-4'
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2',
                    'extraneous-top-package-4'
                }) + sorted({
                    'extraneous-sub-package-2',
                    'extraneous-sub-package-3',
                    'extraneous-sub-sub-package-1',
                    'extraneous-sub-sub-package-2',
                })),
            ),
            extraneous.stdout.decode('utf8')
        )

    def test_full(self):
        extraneous = self.subcmd(
            '`which extraneous.py` -f',
            coverage=True
        )
        self.assertMultiLineEqual(
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                        'extraneous',
                        'setuptools',
                        'extraneous-top-package-4'
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2',
                    'extraneous',
                    'setuptools',
                    'extraneous-top-package-4'
                }) + sorted({
                    'extraneous-sub-package-2',
                    'ansicolors',
                    'pipdeptree',
                    'pip',
                    'extraneous-sub-package-3',
                    'extraneous-sub-sub-package-1',
                    'extraneous-sub-sub-package-2',
                })),
            ),
            extraneous.stdout.decode('utf8')
        )

    def test_exclude_top(self):
        extraneous = self.subcmd(
            '`which extraneous.py` -e extraneous-top-package-2 -e extraneous-top-package-4',
            coverage=True
        )
        self.assertMultiLineEqual(
            '',
            extraneous.stdout.decode('utf8')
        )

    def test_exclude_sub(self):
        extraneous = self.subcmd(
            '`which extraneous.py` -e extraneous-sub-package-2 -e extraneous-sub-package-3',
            coverage=True
        )
        self.assertMultiLineEqual(
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                        'extraneous-top-package-4'
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2',
                    'extraneous-top-package-4',
                }) + sorted({
                })),
            ),
            extraneous.stdout.decode('utf8')
        )

    def test_include(self):
        with TemporaryDirectory() as other_req_dir:
            other_req_name = os.path.join(other_req_dir, 'requirements.txt')
            with open(other_req_name, mode='w+') as other_req:
                other_req.write('extraneous-top-package-2\ncoverage\n')
            up_one = os.path.join(self.cwd_path, '..')
            extraneous = self.subcmd(
                '`which extraneous.py` -v -i {other_req_dir}'.format(other_req_dir=other_req_dir),
                cwd_path=up_one,
                coverage=True
            )
            self.assertMultiLineEqual(
                'reading installed from:\n\t{site_packages}\n'
                'reading requirements from:\n\t{requirements}\n'
                '{extraneous}\n'
                'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                    site_packages=self.get_sitepackages_for_venv(cwd_path=up_one),
                    requirements='\n\t'.join([
                        other_req_name
                    ]),
                    extraneous=color(
                        'extraneous packages:\n\t{}'.format(' '.join(sorted({
                            'extraneous-top-package-1',
                            'extraneous-top-package-3',
                            'extraneous-top-package-4'
                        }))),
                        fg='yellow'
                    ),
                    uninstall=' '.join(sorted({
                        'extraneous-top-package-1',
                        'extraneous-top-package-3',
                        'extraneous-top-package-4'
                    }) + sorted({
                        'extraneous-sub-package-3',
                        'extraneous-sub-sub-package-1',
                        'extraneous-sub-sub-package-2',
                    })),
                ),
                extraneous.stdout.decode('utf8')
            )

    def test_zzz_last_zzz_installed_editable(self):
        self.pip_install(
            'git+ssh://git@github.com/arrai-innovations/transmogrifydict.git#egg=transmogrifydict',
            editable=True
        )
        extraneous = self.subcmd(
            '`which extraneous.py`',
            coverage=True
        )
        self.assertMultiLineEqual(
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                        'transmogrifydict',
                        'extraneous-top-package-4'
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2',
                    'transmogrifydict',
                    'extraneous-top-package-4'
                }) + sorted({
                    'extraneous-sub-package-2',
                    'six',
                    'extraneous-sub-package-3',
                    'extraneous-sub-sub-package-1',
                    'extraneous-sub-sub-package-2',
                })),
            ),
            extraneous.stdout.decode('utf8')
        )
        with open('{cwd_path}/local_requirements.txt'.format(cwd_path=self.cwd_path), mode='w') as w:
            w.write(
                '-e git+ssh://git@github.com/arrai-innovations/transmogrifydict.git#egg=transmogrifydict\n'
            )
        extraneous = self.subcmd(
            '`which extraneous.py`',
            coverage=True
        )
        self.assertMultiLineEqual(
            '{extraneous}\n'
            'uninstall via:\n\tpip uninstall -y {uninstall}\n'.format(
                extraneous=color(
                    'extraneous packages:\n\t{}'.format(' '.join(sorted({
                        'extraneous-top-package-2',
                        'extraneous-top-package-4'
                    }))),
                    fg='yellow'
                ),
                uninstall=' '.join(sorted({
                    'extraneous-top-package-2',
                    'extraneous-top-package-4'
                }) + sorted({
                    'extraneous-sub-package-2',
                    'extraneous-sub-package-3',
                    'extraneous-sub-sub-package-1',
                    'extraneous-sub-sub-package-2',
                })),
            ),
            extraneous.stdout.decode('utf8')
        )
