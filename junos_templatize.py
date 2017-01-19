#!/usr/bin/env python

# reads a junos config and outputs a template and variables file
import argparse
import os
import re
import sys
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--config-file', '-c', help='configuration file', dest="config_file")
parser.add_argument('--file', '-f', help='Junos configuration in curly bracket notation')
args = parser.parse_args()

if args.config_file is None or args.file is None:
    print parser.print_help()
    sys.exit(1)

jt_config_file = args.config_file
junos_config_file = args.file

state = list()
jt_config = dict()
results = dict()

output_template = None


def process_line(line):
    variable_name = None
    new_line = line
    stanza_pattern = "(.*) {"
    stanza_match = re.match(stanza_pattern, line)
    if stanza_match:
        limb = stanza_match.groups()[0]
        cleaned = limb.strip()
        state.append(cleaned)
        variable_name = match_state(node_value=cleaned)
        if variable_name is not None:
            leading_whitespace = ''
            leading_whitespace_match = re.match('(\s+).* {', line)
            if leading_whitespace_match:
                leading_whitespace = leading_whitespace_match.groups()[0]

            new_line = re.sub(stanza_pattern, '%s{{ %s }} {' % (leading_whitespace, variable_name), line)

    else:
        end_stanza_match = re.match(".*}", line)
        if end_stanza_match:
            if len(state):
                write_line_to_template(line)
                state.pop()
                return
        else:
            node_match = re.match("\s+(\S+)\s(.+);", line)
            if node_match:
                node_name = node_match.groups()[0]
                node_value = node_match.groups()[1]
                state.append(node_name)
                variable_name = match_state(node_value=node_value)
                state.pop()
                if variable_name is not None:
                    new_line = re.sub("%s %s;" % (node_name, node_value), '%s {{ %s }};' % (node_name, variable_name),
                                      line)

    write_line_to_template(new_line)


def match_state(node_value=''):
    if jt_config["debug"]:
        print state

    for variable in jt_config["variablize"]:
        path = variable["path"]
        variable_name = variable["name"]

        if len(state) > len(path):
            # no need to go any deeper
            # print "going no further %s %s" % (len(state), len(path))
            continue

        index = 0
        skip = False
        for path_part in path:

            if len(state) == 0:
                skip = True
                break

            elif len(state) > 0 and index > len(state) - 1:
                skip = True
                break

            if not re.match(path_part, state[index]):
                # print "not here %s %s" % (path_part, state[index])
                skip = True
                break

            index += 1

        if skip:
            # jump to next iter, or exit for loop
            continue

        # we have a match!
        if variable_name in results:
            variable_instance_name = variable_name + "_" + str(len(results[variable_name]))
        else:
            variable_instance_name = variable_name + "_0"
            results[variable_name] = list()

        r = dict()
        r["name"] = variable_instance_name
        r["value"] = node_value

        results[variable_name].append(r)
        if jt_config["debug"]:
            print state

        return variable_instance_name

    # no matches
    return None


def write_line_to_template(line):
    global output_template

    should_log = False

    if 'all' in jt_config["template_stanzas"]:
        should_log = True
    else:
        for stanza in jt_config["template_stanzas"]:
            if stanza in state:
                should_log = True
                break

    if should_log:
        if output_template is None:
            output_template = open(jt_config["template_name"], "w")

        output_template.writelines(line)


def consolidate_matches():
    global output_template
    output_template.close()
    consolidated_output = open(jt_config["template_name"], "r")
    ots = consolidated_output.read()
    for n in results:
        for r in results[n]:
            ots = ots.replace(r["value"], '{{ %s }}' % r["name"])

    consolidated_output.close()
    with open(jt_config["template_name"], "w") as output_template:
        output_template.write(ots)


def load_configuration():
    global jt_config
    if not os.path.exists(jt_config_file):
        print "Could not load configuration"
        sys.exit(1)
    with open(jt_config_file) as jtc:
        jt_config = yaml.load(jtc.read())


def write_results_file():
    results_file_name = jt_config["template_vars"]
    with open(results_file_name, 'w') as rf:
        rf.write("---\n")
        rf.write("\n")
        for k in results.keys():
            for r in results[k]:
                rf.writelines("%s: %s\n" % (r["name"], r["value"]))


load_configuration()
with open(junos_config_file) as config:
    for line in config:
        process_line(line)

consolidate_matches()
write_results_file()
print "template written to %s" % jt_config["template_name"]
print "template vars written to %s" % jt_config["template_vars"]

