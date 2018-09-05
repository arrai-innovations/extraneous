#!/bin/env python
# Copyright (C) 2018 Arrai Innovations Inc. - All Rights Reserved
import os
import re
from itertools import chain

from colors import color
from pip._internal import get_installed_distributions
from pip._internal.utils.misc import dist_is_editable
from pipdeptree import build_dist_index, construct_tree, reverse_tree

flatten = chain.from_iterable
re_operator = re.compile(r'[>=]')
__version__ = '1.0.0'


def parse_requirement(line):
    if line.startswith('-e'):
        return line
    return re_operator.split(line)[0]


def read_requirements(verbose=True):
    cwd = os.getcwd()
    if verbose:
        print('reading requirements from:')
    reqs = set()
    rnames = ['requirements.txt', 'local_requirements.txt', 'test_requirements.txt']
    for rname in rnames:
        try:
            with open(rname) as rfile:
                if verbose:
                    print('\t{cwd}/{rname}'.format(cwd=cwd, rname=rname))
                reqs |= set(parse_requirement(line) for line in rfile.read().split('\n') if line)
        except FileNotFoundError:
            pass
    return reqs


def read_installed(verbose=True):
    from site import getsitepackages
    site_package_dirs = getsitepackages()
    if verbose:
        print('reading installed from:\n\t{}'.format('\n\t'.join(site_package_dirs)))
    pkgs = get_installed_distributions()
    dist_index = build_dist_index(pkgs)
    tree = construct_tree(dist_index)
    branch_keys = set(r.key for r in flatten(tree.values()))
    nodes = [p for p in tree.keys() if p.key not in branch_keys]
    project_names = set(p.project_name for p in nodes)
    editable_packages = dict((p.render(frozen=True), p.project_name) for p in nodes if dist_is_editable(p._obj))
    return set(project_names), editable_packages, tree


def package_tree_to_name_tree(tree):
    return {k.project_name: set(i.project_name for i in v) for k, v in tree.items()}


def find_requirements_unique_to_projects(tree, root_package_names_to_uninstall):
    name_tree = package_tree_to_name_tree(tree)
    name_rtree = package_tree_to_name_tree(reverse_tree(tree))
    packages_to_uninstall = set(name for name in root_package_names_to_uninstall)

    def add_to_uninstall(packages):
        for package in packages:
            required_by = name_rtree.get(package, set())
            other_required_by = required_by - root_package_names_to_uninstall
            if not other_required_by:
                packages_to_uninstall.add(package)
                p_requirements = name_tree.get(package, None)
                if p_requirements:
                    add_to_uninstall(p_requirements)
    add_to_uninstall(root_package_names_to_uninstall)
    return packages_to_uninstall


if __name__ == '__main__':
    args_verbose = True
    installed, editable, tree = read_installed(args_verbose)
    requirements = read_requirements(args_verbose)
    for frozen, name in editable.items():
        if frozen in requirements:
            requirements.remove(frozen)
            requirements.add(name)
    never_extraneous = {'psycopg2', 'pipdeptree', 'pip', 'setuptools'}
    extraneous = installed - requirements - never_extraneous
    if extraneous:
        print(color('extraneous packages:\n\t{}'.format(' '.join(extraneous)), fg='yellow'))
        uninstall = find_requirements_unique_to_projects(tree, extraneous) - never_extraneous
        print('uninstall via:\n\tpip uninstall -y {}'.format(' '.join(uninstall)))
