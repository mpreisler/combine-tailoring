#!/usr/bin/python2

# Copyright 2016 Red Hat Inc., Durham, North Carolina.
# All Rights Reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:
#   Martin Preisler <mpreisle@redhat.com>

import argparse
import sys
try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    import cElementTree as ElementTree


XCCDF12_NS = "http://checklists.nist.gov/xccdf/1.2"


def main():
    parser = argparse.ArgumentParser(
        description="Combine XCCDF or datastream and a tailoring file to form "
                    "just one file that contains all the profiles."
    )
    parser.add_argument(
        "SCAP_INPUT", type=argparse.FileType("r"),
        help="XCCDF or Source DataStream"
    )
    parser.add_argument(
        "TAILORING_FILE", type=argparse.FileType("r"),
        help="XCCDF 1.2 Tailoring file to insert"
    )
    parser.add_argument(
        "--output", type=argparse.FileType("w"), required=False,
        default=sys.stdout,
        help="Resulting XCCDF or Source DataStream"
    )

    args = parser.parse_args()

    input_tree = ElementTree.ElementTree()
    input_tree.parse(args.SCAP_INPUT)
    input_root = input_tree.getroot()

    tailoring_tree = ElementTree.ElementTree()
    tailoring_tree.parse(args.TAILORING_FILE)
    tailoring_root = tailoring_tree.getroot()

    benchmarks = list(input_root.findall(".//{%s}Benchmark" % (XCCDF12_NS)))

    if len(benchmarks) != 1:
        raise RuntimeError(
            "Expected exactly one Benchmark in the file, instead found %i "
            "benchmarks." % (len(benchmarks))
        )

    benchmark = benchmarks[0]
    profile_insert_point = None
    for profile in benchmark.findall("./{%s}Profile" % (XCCDF12_NS)):
        profile_insert_point = profile

    for profile_to_add in \
            tailoring_root.findall(".//{%s}Profile" % (XCCDF12_NS)):

        index = list(benchmark).index(profile_insert_point)
        benchmark.insert(index + 1, profile_to_add)
        profile_insert_point = profile_to_add

    input_tree.write(args.output)


if __name__ == "__main__":
    main()
