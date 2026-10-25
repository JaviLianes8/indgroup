// Format values with Intl.NumberFormat on demand, as a live oracle for the tests.
//
// Reads a JSON array of [tag, grouping, value] from stdin and writes a JSON object with the
// Node, ICU and CLDR versions and, for each case, [resolved locale, output]. Values are
// decimal strings formatted exactly, with as many fraction digits as they have, and Latin
// digits (-u-nu-latn), as scripts/intl_reference.mjs does.
//
//     node scripts/intl_oracle.mjs < cases.json

import { readFileSync } from "node:fs";

const cases = JSON.parse(readFileSync(0, "utf8"));
const results = cases.map(([tag, grouping, value]) => {
  const point = value.indexOf(".");
  const digits = point < 0 ? 0 : value.length - point - 1;
  try {
    const formatter = new Intl.NumberFormat(`${tag}-u-nu-latn`, {
      useGrouping: grouping === "off" ? false : grouping,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
    const resolved = formatter.resolvedOptions().locale.replace(/-u-nu-latn$/, "");
    return [resolved, formatter.format(value)];
  } catch (error) {
    return [null, error.name];
  }
});
const { node, icu, cldr } = process.versions;
process.stdout.write(JSON.stringify({ node, icu, cldr, results }));
