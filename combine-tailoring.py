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
#   Birol Bilgin <bbilgin@redhat.com>

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
        "--output", type=argparse.FileType("wb"), required=False,
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

    if len(benchmarks) == 0:
        sys.stderr.write(
            "There is no Benchmark elements in input file %s \n" % (args.SCAP_INPUT.name))
        sys.exit(1)

    t_profiles = tailoring_root.findall(".//{%s}Profile" % (XCCDF12_NS))

    if len(t_profiles) == 0:
        sys.stderr.write(
            "There is no Profile elements in the tailored file %s \n" % (args.TAILORING_FILE.name))
        sys.exit(1)

    # As far as my tests goes you cannot have a tailored file that has
    # profiles belongs to different benchmark checklists
    # we just need to figure out which benchmark tailored profiles belongs to

    b_index = -1
    extended_profile = t_profiles[0].get("extends")
    benchmark = None
    profile_insert_point = None

    for i, bench in enumerate(benchmarks):
        if b_index != -1:
            break
        for profile in bench.findall("./{%s}Profile" % (XCCDF12_NS)):
            if b_index == -1 and \
                    (profile.get("id") == extended_profile or
                     extended_profile is None):
                b_index = i
                benchmark = benchmarks[i]
            profile_insert_point = profile

    if profile_insert_point is None:
        sys.stderr.write(
            "Couldn't find a suitable Profile insert point in the input file. "
            "Please check the @extends attribute in your tailoring file to "
            "make sure there is a matching profile in the input file. "
            "Make sure there is at least one profile in the input file. It can "
            "be empty or have just one select.")
        sys.exit(1)

    for profile_to_add in t_profiles:
        index = list(benchmark).index(profile_insert_point)
        benchmark.insert(index + 1, profile_to_add)
        profile_insert_point = profile_to_add

    input_tree.write(args.output)


if __name__ == "__main__":
    main()
