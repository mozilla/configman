#!/usr/bin/env python
import configman
parser = configman.ArgumentParser()
parser.add_argument("echo")
args = parser.parse_args()
print args.echo
