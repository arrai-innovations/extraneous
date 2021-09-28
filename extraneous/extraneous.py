#!/bin/env python
# Copyright (C) 2018 Arrai Innovations Inc. - All Rights Reserved
import argparse
import glob
import os
import re
from itertools import chain

# noinspection PyUnresolvedReferences,PyPackageRequirements
from colors import color
from pipdeptree import PackageDAG

try:
    # noinspection PyPackageRequirements,PyCompatibility
    from pip._internal.utils.misc import get_installed_distributions, dist_is_editable
except ImportError:
    # noinspection PyPackageRequirements,PyCompatibility
    from pip import get_installed_distributions, dist_is_editable

flatten = chain.from_iterable
re_operator = re.compile(r'[>=]')


def normalize_package_name(name):
    """
    https://www.python.org/dev/peps/pep-0503/#normalized-names
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement(line):
    if line.startswith('-e'):
        return line
    return re_operator.split(line)[0]


def read_requirements(verbose=True, include=None):
    cwd = os.getcwd()
    if verbose:
        print('reading requirements from:')
    include_files = sorted(glob.glob('*requirements*.txt'))
    if include:
        for include_dir in include:
            include_files += sorted(glob.glob(os.path.join(include_dir, '*requirements*.txt')))
    reqs = set()
    for rname in include_files:
        if os.path.isabs(rname):
            path = rname
        else:
            path = os.path.relpath(rname, cwd)
        try:
            with open(path) as rfile:
                if verbose:
                    print('\t{}'.format(path))
                reqs |= set(parse_requirement(line) for line in rfile.read().split('\n') if line)
        except FileNotFoundError:
            if verbose:
                print('\t{} (Not Found)'.format(path))
    if not reqs:
        raise ValueError('No requirements found.{}'.format(
            '' if verbose else ' Use -v for more information.'
        ))
    return {normalize_package_name(x) for x in reqs}


def read_installed(verbose=True):
    cwd = os.getcwd()
    if verbose:
        try:
            # virtual environment with venv in python 3.3+
            from site import getsitepackages
            site_package_dirs = getsitepackages()
        except ImportError:
            # virtual environment with virtualenv
            # https://github.com/pypa/virtualenv/issues/228
            from distutils.sysconfig import get_python_lib
            site_package_dirs = [get_python_lib()]
        print('reading installed from:\n\t{}'.format(
            '\n\t'.join([os.path.relpath(x, cwd) for x in site_package_dirs])
        ))
    pkgs = get_installed_distributions()
    tree = PackageDAG.from_pkgs(pkgs)
    branch_keys = set(r.key for r in flatten(tree.values()))
    nodes = [p for p in tree.keys() if p.key not in branch_keys]
    project_names = set(normalize_package_name(p.project_name) for p in nodes)
    editable_packages = set(normalize_package_name(p.project_name) for p in nodes if dist_is_editable(p._obj))
    return set(project_names), editable_packages, tree


def package_tree_to_name_tree(tree):
    return {normalize_package_name(k.project_name): set(normalize_package_name(i.project_name) for i in v) for k, v in
            tree.items()}


def find_requirements_unique_to_projects(tree, requirements, root_package_names_to_uninstall, exclude_packages):
    name_tree = package_tree_to_name_tree(tree)
    name_rtree = package_tree_to_name_tree(tree.reverse())
    packages_to_uninstall = set(name for name in root_package_names_to_uninstall)

    def add_to_uninstall(packages):
        for package in packages:
            if package in requirements or package in exclude_packages:
                continue
            required_by = name_rtree.get(package, set())
            other_required_by = required_by - packages_to_uninstall
            if not other_required_by:
                packages_to_uninstall.add(package)
                p_requirements = name_tree.get(package, None)
                if p_requirements:
                    add_to_uninstall(p_requirements)

    add_to_uninstall(root_package_names_to_uninstall)
    return packages_to_uninstall


def main(*args):
    default_not_extraneous = ['extraneous', 'pipdeptree', 'pip', 'setuptools']
    parser = argparse_class(
        prog='extraneous.py',
        description='Identifies packages that are installed but not defined in requirements files. Prints the'
                    " 'pip uninstall' command that removes these extraneous packages and any non-common"
                    " dependencies. Looks for packages matching '*requirements*.txt' in the current working"
                    ' directory.'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Prints installed site-package folders and requirements files.'
    )
    parser.add_argument(
        '--include', '-i',
        metavar='paths',
        action='append',
        help="Additional directories to look for '*requirements*.txt' files in."
    )
    parser.add_argument(
        '--exclude', '-e',
        metavar='names',
        action='append',
        default=[],
        help='Package names to not consider extraneous.'
             ' {} are not considered extraneous packages.'.format(default_not_extraneous)
    )
    parser.add_argument(
        '--full', '-f',
        action='store_true',
        help='Allows {} as extraneous packages.'.format(default_not_extraneous)
    )
    if args:
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()
    installed, editable, tree = read_installed(parsed_args.verbose)
    requirements = read_requirements(
        parsed_args.verbose,
        include=parsed_args.include
    )
    for name in editable:
        for requirement in list(requirements):
            if requirement.endswith('#egg={}'.format(name)):
                requirements.remove(requirement)
                requirements.add(name)
    not_extraneous = set(parsed_args.exclude)
    if not parsed_args.full:
        not_extraneous |= set(default_not_extraneous)
    extraneous = installed - requirements - not_extraneous
    uninstall = set()
    if extraneous:
        print(color(
            'extraneous packages:\n\t{}'.format(' '.join(sorted(extraneous))),
            fg='yellow'
        ))
        uninstall = find_requirements_unique_to_projects(tree, requirements, extraneous, not_extraneous) - extraneous
        print('uninstall via:\n\tpip uninstall -y {}'.format(
            ' '.join(sorted(extraneous) + sorted(uninstall))
        ))
    return extraneous, uninstall


class BadArgumentError(ValueError):
    pass


class NoExitArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise BadArgumentError(self.format_usage(), message)


argparse_class = NoExitArgumentParser
if __name__ == '__main__':
    argparse_class = argparse.ArgumentParser
    main()
