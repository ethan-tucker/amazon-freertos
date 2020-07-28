from __future__ import print_function
import sys
import os

from kconfiglib import Kconfig, BOOL, TRISTATE, TRI_TO_STR


if len(sys.argv) < 4:
    sys.exit("usage: merge_config.py Kconfig merged_config config1 [config2 ...]")

kconf = Kconfig(sys.argv[1], suppress_traceback=True)

# Enable warnings for assignments to undefined symbols
kconf.warn_assign_undef = True

# (This script uses alldefconfig as the base. Other starting states could be
# set up here as well. The approach in examples/allnoconfig_simpler.py could
# provide an allnoconfig starting state for example.)

# Disable warnings generated for multiple assignments to the same symbol within
# a (set of) configuration files. Assigning a symbol multiple times might be
# done intentionally when merging configuration files.
kconf.warn_assign_override = False
kconf.warn_assign_redun = False

# Create a merged configuration by loading the fragments with replace=False.
# load_config() and write_config() returns a message to print.
for config in sys.argv[3:]:
    print(kconf.load_config(config, replace=False))

# Write the merged configuration
print(kconf.write_config(sys.argv[2]))

# Print warnings for symbols whose actual value doesn't match the assigned
# value
for sym in kconf.defined_syms:
    # Was the symbol assigned to?
    if sym.user_value is not None:
        # Tristate values are represented as 0, 1, 2. Having them as
        # "n", "m", "y" is more convenient here, so convert.
        if sym.type in (BOOL, TRISTATE):
            user_value = TRI_TO_STR[sym.user_value]
        else:
            user_value = sym.user_value

        if user_value != sym.str_value:
            print("warning: {} was assigned the value '{}' but got the "
                  "value '{}' -- check dependencies".format(
                      sym.name_and_loc, user_value, sym.str_value),
                  file=sys.stderr)